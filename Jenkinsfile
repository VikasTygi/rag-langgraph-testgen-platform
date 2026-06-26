pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REPOSITORY = 'rag-testgen-api'
        S3_ARTIFACT_BUCKET = 'rag-testgen-artifacts-989571800722-ap-south-1'
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

                    echo "Python:"
                    python3 --version

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
                        python3 -m venv .venv
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

                    echo "IMAGE_TAG_BUILD=${env.IMAGE_TAG_BUILD}"
                    echo "IMAGE_TAG_SHA=${env.IMAGE_TAG_SHA}"
                    echo "IMAGE_TAG_DEV=${env.IMAGE_TAG_DEV}"
                }
            }
        }

        stage('Login to ECR') {
            steps {
                sh '''
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
                '''
            }
        }

        stage('Setup Buildx') {
            steps {
                sh '''
                    docker buildx create --name rag-builder --use || docker buildx use rag-builder
                    docker buildx inspect --bootstrap
                '''
            }
        }

        stage('Build and Push linux/amd64 Image') {
            steps {
                sh '''
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
            echo "SUCCESS: Docker linux/amd64 image pushed to ECR"
            echo "Image: ${IMAGE_TAG_BUILD}"
        }

        failure {
            echo "FAILED: Check pytest, ruff, bandit, Docker, ECR, or IAM role permissions"
        }

        always {
            cleanWs()
        }
    }
}