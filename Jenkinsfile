pipeline {
	agent {
		docker {
			image 'python:2.7'
			args '-u root'
		}
	}

	stages {

		stage('Linting') {
			steps {
				sh 'pip install -r requirements.txt'
				sh 'for i in *.yaml; do pykwalify -d $i -s .schema.yaml; done'
			}
		}

		stage('Updated Trusted Repositories') {
			when {
				branch 'master'
			}

			steps {
				sh 'pip install -r requirements.txt'
				sh 'python scripts/update-trusted.py'
			}
		}

	}
}
