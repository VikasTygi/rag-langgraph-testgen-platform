pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REPOSITORY = 'rag-testgen-api'
        S3_ARTIFACT_BUCKET = 'rag-testgen-artifacts-989571800722-ap-south-1'
        ENVIRONMENT = 'test'
        DISABLE_RATE_LIMIT = 'true'
        DISABLE_REDIS = 'true'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check Tools') {
            steps {
                sh '''
                    echo "User:"
                    whoami

                    echo "Workspace:"
                    pwd

                    echo "Branch:"
                    echo "BRANCH_NAME=${BRANCH_NAME}"
                    echo "CHANGE_ID=${CHANGE_ID}"
                    echo "CHANGE_BRANCH=${CHANGE_BRANCH}"
                    echo "CHANGE_TARGET=${CHANGE_TARGET}"

                    echo "Python:"
                    python3.11 --version

                    echo "Docker:"
                    docker --version

                    echo "Buildx:"
                    docker buildx version

                    echo "AWS:"
                    aws --version
                    aws sts get-caller-identity
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                dir('backend') {
                    sh '''

                        export TMPDIR=/var/lib/jenkins/tmp
                        export PIP_CACHE_DIR=/var/lib/jenkins/.cache/pip
                        
                        rm -rf .venv
                        python3.11 -m venv .venv
                        . .venv/bin/activate

                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install ruff bandit
                    '''
                }
            }
        }

        stage('Pytest') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        pytest -v
                    '''
                }
            }
        }

        stage('Ruff') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        ruff check app tests
                    '''
                }
            }
        }

        stage('Bandit') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        bandit -r app -ll
                    '''
                }
            }
        }

        stage('Prepare Image Tags') {
            steps {
                script {
                    env.ACCOUNT_ID = sh(
                        script: "aws sts get-caller-identity --query Account --output text",
                        returnStdout: true
                    ).trim()

                    env.ECR_REGISTRY = "${env.ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"
                    env.ECR_IMAGE = "${env.ECR_REGISTRY}/${env.ECR_REPOSITORY}"

                    env.GIT_SHORT_SHA = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()

                    env.IMAGE_TAG_BUILD = "${env.ECR_IMAGE}:${env.BUILD_NUMBER}"
                    env.IMAGE_TAG_SHA = "${env.ECR_IMAGE}:${env.GIT_SHORT_SHA}"
                    env.IMAGE_TAG_DEV = "${env.ECR_IMAGE}:dev-latest"

                    echo "ACCOUNT_ID=${env.ACCOUNT_ID}"
                    echo "ECR_REGISTRY=${env.ECR_REGISTRY}"
                    echo "ECR_IMAGE=${env.ECR_IMAGE}"
                    echo "IMAGE_TAG_BUILD=${env.IMAGE_TAG_BUILD}"
                    echo "IMAGE_TAG_SHA=${env.IMAGE_TAG_SHA}"
                    echo "IMAGE_TAG_DEV=${env.IMAGE_TAG_DEV}"
                }
            }
        }

        stage('Setup Buildx') {
            steps {
                sh '''
                    docker buildx create --name rag-builder --driver docker-container --use || docker buildx use rag-builder
                    docker buildx inspect --bootstrap
                '''
            }
        }

        stage('Build linux/amd64 Image - Validate Only') {
            when {
                expression { env.BRANCH_NAME != 'main' }
            }
            steps {
                sh '''
                    echo "Validation build only. This branch will NOT push image to ECR."
                    echo "BRANCH_NAME=${BRANCH_NAME}"

                    docker buildx build \
                      --platform linux/amd64 \
                      -t rag-testgen-api:${BUILD_NUMBER} \
                      --load \
                      ./backend
                '''
            }
        }

        stage('Ensure ECR Repository') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                sh '''
                    aws ecr describe-repositories \
                      --repository-names ${ECR_REPOSITORY} \
                      --region ${AWS_REGION} || \
                    aws ecr create-repository \
                      --repository-name ${ECR_REPOSITORY} \
                      --region ${AWS_REGION}
                '''
            }
        }

        stage('Login to ECR') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                sh '''
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
                '''
            }
        }

        stage('Build and Push linux/amd64 Image') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                sh '''
                    echo "Main branch build. Image will be pushed to ECR."

                    docker buildx build \
                      --platform linux/amd64 \
                      -t ${IMAGE_TAG_BUILD} \
                      -t ${IMAGE_TAG_SHA} \
                      -t ${IMAGE_TAG_DEV} \
                      --push \
                      ./backend
                '''
            }
        }

        stage('Archive Image Info') {
            when {
                expression { env.BRANCH_NAME == 'main' }
            }
            steps {
                sh '''
                    mkdir -p artifacts

                    cat > artifacts/image-info.txt << EOF
ECR_IMAGE=${ECR_IMAGE}
BUILD_NUMBER_TAG=${IMAGE_TAG_BUILD}
GIT_SHA_TAG=${IMAGE_TAG_SHA}
DEV_LATEST_TAG=${IMAGE_TAG_DEV}
GIT_COMMIT=${GIT_COMMIT}
GIT_SHORT_SHA=${GIT_SHORT_SHA}
AWS_REGION=${AWS_REGION}
BRANCH_NAME=${BRANCH_NAME}
BUILD_NUMBER=${BUILD_NUMBER}
EOF

                    cat artifacts/image-info.txt

                    aws s3 cp artifacts/image-info.txt \
                      s3://${S3_ARTIFACT_BUCKET}/jenkins/rag-testgen-api/${BUILD_NUMBER}/image-info.txt
                '''

                archiveArtifacts artifacts: 'artifacts/image-info.txt', fingerprint: true
            }
        }
    }

    post {
        success {
            script {
                if (env.BRANCH_NAME == 'main') {
                    echo "SUCCESS: Main branch validated and Docker linux/amd64 image pushed to ECR."
                    echo "Image: ${env.IMAGE_TAG_BUILD}"
                } else {
                    echo "SUCCESS: Branch/PR validation passed. Image was built locally but NOT pushed to ECR."
                    echo "Branch: ${env.BRANCH_NAME}"
                }
            }
        }

        failure {
            echo "FAILED: Check pytest, ruff, bandit, Docker, ECR, IAM role, or dependency installation."
        }

        always {
            cleanWs()
        }
    }
}