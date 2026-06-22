pipeline {
    agent any

    environment {
        APP_NAME = "rag-testgen-api"
        IMAGE_TAG = "${BUILD_NUMBER}"
        DOCKER_IMAGE = "${APP_NAME}:${IMAGE_TAG}"
        PYTHON_VERSION = "python3.11"
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                dir('backend') {
                    sh '''
                        ${PYTHON_VERSION} -m venv .venv
                        . .venv/bin/activate
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install ruff bandit pytest
                    '''
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        mkdir -p reports
                        pytest -v tests \
                          --ignore=tests/test_rag.py \
                          --ignore=tests/test_langgraph_workflow.py \
                          --junitxml=reports/unit-tests.xml
                    '''
                }
            }
            post {
                always {
                    junit 'backend/reports/unit-tests.xml'
                }
            }
        }

        stage('Run RAG Tests') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        mkdir -p reports
                        pytest -v tests/test_rag.py \
                          --junitxml=reports/rag-tests.xml
                    '''
                }
            }
            post {
                always {
                    junit 'backend/reports/rag-tests.xml'
                }
            }
        }

        stage('Run LangGraph Tests') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        mkdir -p reports
                        pytest -v tests/test_langgraph_workflow.py \
                          --junitxml=reports/langgraph-tests.xml
                    '''
                }
            }
            post {
                always {
                    junit 'backend/reports/langgraph-tests.xml'
                }
            }
        }

        stage('Run Security Checks') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate

                        echo "Running Ruff lint check..."
                        ruff check app tests

                        echo "Running Bandit security scan..."
                        bandit -r app -f json -o reports/bandit-report.json
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'backend/reports/bandit-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                dir('backend') {
                    sh '''
                        docker build -t ${DOCKER_IMAGE} .
                        docker images | grep ${APP_NAME}
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'backend/reports/*.xml, backend/reports/*.json', allowEmptyArchive: true
            cleanWs()
        }

        success {
            echo "CI pipeline passed. Docker image built: ${DOCKER_IMAGE}"
        }

        failure {
            echo "CI pipeline failed. Check test, lint, security, or Docker build logs."
        }
    }
}
