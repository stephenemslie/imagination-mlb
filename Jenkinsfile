pipeline {
    agent any
    environment {
        COMPOSE_FILE = 'docker-compose.yml:docker-compose.prod.yml'
    }
    stages {
        stage('Build') {
            steps {
                sh 'docker-compose build django postgres-backup'
                sh 'docker-compose push django postgres-backup'
            }
        }
        stage('Test') {
            steps {
                sh 'docker-compose run --rm django test'
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker-compose up -d --no-deps django'
            }
        }
    }
}
