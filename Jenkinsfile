pipeline {
    agent any

    environment {
        PATH = "/opt/homebrew/bin:/opt/homebrew/opt/python@3.11/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
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
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        pytest -v
                    '''
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
                        bandit -r app
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t rag-testgen-api:local ./backend
                '''
            }
        }
    }

    post {
        success {
            echo 'CI pipeline passed.'
        }

        failure {
            echo 'CI pipeline failed. Check test, lint, security, or Docker build logs.'
        }

        always {
            archiveArtifacts artifacts: '**/*.xml, **/reports/**', allowEmptyArchive: true
        }
    }
}
