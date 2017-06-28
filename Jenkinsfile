pipeline {
    agent any
    environment {
        RELEASE_AUTH=credentials('RELEASE_AUTH')
        DJANGO_TAG='localhost:5000/mlb_django:latest'
    }
    stages {
        stage('Build') {
            steps {
                sh 'curl -L -o /usr/local/bin/jp https://github.com/jmespath/jp/releases/download/0.1.2/jp-linux-amd64 && chmod +x /usr/local/bin/jp'
                sh 'curl -L https://github.com/docker/compose/releases/download/1.14.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose'
                sh './get-leaderboard.sh'
                sh 'docker-compose -f docker-compose.yml -f docker-compose.prod.yml build django'
            }
        }
        stage('Test') {
            steps {
                sh 'docker-compose stop && docker-compose rm -f'
                sh 'docker-compose -f docker-compose.yml run -e RECALL_DISABLE=True -e DATABASE_URL=psql://postgres:postgres@postgres:5432/postgres -e SECRET_KEY=testrun --rm django test'
                sh 'docker-compose stop && docker-compose rm -f'
            }
        }
        stage('Deploy') {
            when {
                expression {
                    return BRANCH_NAME == 'master'
                }
            }
            steps {
                sh 'docker tag mlb_django:latest $DJANGO_TAG'
                sh 'docker push $DJANGO_TAG'
                sh 'docker service update --image $DJANGO_TAG django-master'
                sh 'docker service update --image $DJANGO_TAG celery'
            }
        }
    }
}
