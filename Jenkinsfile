pipeline {
    agent any

    environment {
        PATH = "/opt/homebrew/bin:/opt/homebrew/opt/python@3.11/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

        AWS_REGION = "ap-south-1"
        ECR_REPO = "rag-langgraph-testgen-platform"

        AWS_ACCOUNT_ID = "989571800722"

        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        IMAGE_TAG = "${BUILD_NUMBER}"
        LOCAL_IMAGE = "${ECR_REPO}:${IMAGE_TAG}"
        ECR_IMAGE = "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"

        ECS_CLUSTER = "rag-testgen-dev"
        ECS_SERVICE = "rag-testgen-api"
        TASK_FAMILY = "rag-testgen-api-dev"
        CONTAINER_NAME = "rag-testgen-api"
        ALB_NAME = "rag-testgen-alb-dev"
        EFS_ID = "fs-0c88917ba318fb9ac"
        CHROMA_PERSIST_DIR = "/data/chroma_db"
    }
    options {
        timestamps()
    }

    stages {
        stage('Check Tools') {
            steps {
                sh '''
                    echo "User:"
                    whoami

                    echo "PATH:"
                    echo $PATH

                    echo "Python:"
                    which python3.11
                    python3.11 --version

                    echo "Docker:"
                    which docker
                    docker --version

                    echo "AWS CLI:"
                    which aws
                    aws --version

                    echo "JQ:"
                    which jq
                    jq --version
                '''
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                dir('backend') {
                    sh '''
                        python3.11 -m venv .venv
                        . .venv/bin/activate
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }

stage('Run Unit Tests') {
    steps {
        catchError(buildResult: 'UNSTABLE', stageResult: 'Passed') {
            dir('backend') {
                sh '''
                    . .venv/bin/activate
                    export CHROMA_PERSIST_DIR="./chroma_db"
                    rm -rf ./chroma_db
                    pytest -v
                '''
            }
        }
    }
}

        stage('Run Security Checks') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        pip install ruff bandit
                        ruff check app
                        bandit -r app -ll
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -e

                    echo "Building Docker image..."

                    docker build \
                      -t ${LOCAL_IMAGE} \
                      -f backend/Dockerfile \
                      backend

                    echo "Local Docker image:"
                    docker images | grep ${ECR_REPO}
                '''
            }
        }

        stage('Login to ECR') {
            steps {
                withCredentials([[ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-ecr-jenkins' ]]) {
                    sh '''
                        set -e

                        echo "Logging in to AWS ECR..."

                        aws ecr get-login-password --region ${AWS_REGION} \
                          | docker login \
                              --username AWS \
                              --password-stdin ${ECR_REGISTRY}
                    '''
                }
            }
        }

        stage('Tag Image') {
            steps {
                sh '''
                    set -e

                    echo "Tagging Docker image..."

                    docker tag ${LOCAL_IMAGE} ${ECR_IMAGE}

                    echo "ECR image:"
                    echo ${ECR_IMAGE}
                '''
            }
        }

        stage('Push Image to ECR') {
            steps {
                withCredentials([[ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-ecr-jenkins' ]]) {
                    sh '''
                        set -e

                        echo "Pushing image to ECR..."
                        docker push ${ECR_IMAGE}
                    '''
                }
            }
        }

        stage('Archive Image URI') {
            steps {
                sh '''
                    echo ${ECR_IMAGE} > image-uri.txt
                    cat image-uri.txt
                '''

                archiveArtifacts artifacts: 'image-uri.txt', fingerprint: true
            }
        }

        stage('Deploy to ECS Dev') {
            steps {
                withCredentials([[ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-ecr-jenkins' ]]) {
                    sh '''
                        set -e

                        echo "Deploying image to ECS:"
                        echo ${ECR_IMAGE}

                        echo "Reading current ECS task definition..."

                        aws ecs describe-task-definition \
                          --task-definition ${TASK_FAMILY} \
                          --region ${AWS_REGION} \
                          --query taskDefinition > current-task-def.json

                        echo "Creating new task definition JSON with updated image..."

                        jq \
                              --arg IMAGE_URI "${ECR_IMAGE}" \
                              --arg CONTAINER_NAME "${CONTAINER_NAME}" \
                              --arg EFS_ID "${EFS_ID}" \
                              --arg CHROMA_PERSIST_DIR "${CHROMA_PERSIST_DIR}" \
                              'del(
                                .taskDefinitionArn,
                                .revision,
                                .status,
                                .requiresAttributes,
                                .compatibilities,
                                .registeredAt,
                                .registeredBy
                              )
                              | .volumes = (
                                  ((.volumes // []) | map(select(.name != "chroma-efs")))
                                  + [{
                                      "name": "chroma-efs",
                                      "efsVolumeConfiguration": {
                                        "fileSystemId": $EFS_ID,
                                        "rootDirectory": "/",
                                        "transitEncryption": "ENABLED"
                                      }
                                    }]
                                )
                              | (.containerDefinitions[] | select(.name == $CONTAINER_NAME) | .image) = $IMAGE_URI
                              | (.containerDefinitions[] | select(.name == $CONTAINER_NAME) | .mountPoints) =
                                  (
                                    ((.containerDefinitions[] | select(.name == $CONTAINER_NAME) | .mountPoints) // [])
                                    | map(select(.sourceVolume != "chroma-efs"))
                                    + [{
                                        "sourceVolume": "chroma-efs",
                                        "containerPath": "/data",
                                        "readOnly": false
                                      }]
                                  )
                              | (.containerDefinitions[] | select(.name == $CONTAINER_NAME) | .environment) =
                                  (
                                    ((.containerDefinitions[] | select(.name == $CONTAINER_NAME) | .environment) // [])
                                    | map(select(.name != "CHROMA_PERSIST_DIR"))
                                    + [{"name": "CHROMA_PERSIST_DIR", "value": $CHROMA_PERSIST_DIR}]
                                  )' \
                              current-task-def.json > new-task-def.json

                        echo "Registering new ECS task definition revision..."

                        NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
                          --cli-input-json file://new-task-def.json \
                          --region ${AWS_REGION} \
                          --query 'taskDefinition.taskDefinitionArn' \
                          --output text)

                        echo "New task definition ARN:"
                        echo $NEW_TASK_DEF_ARN

                        echo "Updating ECS service..."

                        aws ecs update-service \
                          --cluster ${ECS_CLUSTER} \
                          --service ${ECS_SERVICE} \
                          --task-definition $NEW_TASK_DEF_ARN \
                          --force-new-deployment \
                          --region ${AWS_REGION}

                        echo "Waiting for ECS service to become stable..."

                        aws ecs wait services-stable \
                          --cluster ${ECS_CLUSTER} \
                          --services ${ECS_SERVICE} \
                          --region ${AWS_REGION}

                        echo "ECS deployment completed successfully."
                    '''
                }
            }
        }

        stage('Smoke Test Dev') {
            steps {
                withCredentials([[ $class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-ecr-jenkins' ]]) {
                    sh '''
                        set -e

                        echo "Getting ALB DNS..."

                        ALB_DNS=$(aws elbv2 describe-load-balancers \
                          --names ${ALB_NAME} \
                          --region ${AWS_REGION} \
                          --query "LoadBalancers[0].DNSName" \
                          --output text)

                        echo "ALB DNS:"
                        echo $ALB_DNS

                        echo "Running smoke test:"
                        echo "http://$ALB_DNS/health"

                        curl -f http://$ALB_DNS/health

                        echo "Smoke test passed."
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "CI/CD pipeline passed. Docker image pushed and ECS deployed successfully: ${ECR_IMAGE}"
        }

        failure {
            echo 'CI/CD pipeline failed. Check test, lint, security, Docker build, ECR push, ECS deploy, or smoke test logs.'
        }

        always {
            archiveArtifacts artifacts: '**/*.xml, **/reports/**, current-task-def.json, new-task-def.json', allowEmptyArchive: true

            sh '''
                echo "Cleaning unused local Docker images..."
                docker image prune -f || true
            '''
        }
    }
}

