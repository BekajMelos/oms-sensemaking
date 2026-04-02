# Local Scanning with Sonarqube

## Dependencies
- Sonar Scanner
  - `brew install sonar-scanner`

Devs can run sonarqube locally to address code quality issues without having to wait for a CI build to complete.

## Starting Sonarqube
Make sure that 'tools' is added to 'COMPOSE_PROFILES' in local.dev.env in the atoms-local-dev project
```
COMPOSE_PROFILES=...,core-api...,tools
```

## Running a Scan

Sonarqube can be tested via going to http://localhost:9900

### Enter the default credentials

Login:
```
admin
```
Password:
```
admin
```

### Create new credentials

Old password:
```
admin
```
New password:
```
Devdevdev#123
```
Confirm new password:
```
Devdevdev#123
```
### Create a project
Choose `Create a local project`

Project display name:
```
sensemaking
```
Then confirm by clicking next
'''
Next
'''
Then click the following
'''
Follows the instance's default
'''

### How do you want to analyze your project
Click
```
Locally
```
Click
```
Generate
```
Click
```
Continue
```
#### Run analysis on your project
What option best describes your build?
```
Other
```
What is your OS?
```
macOS
```

### Run the scanner
Ensure dependencies are installed and go to the project root in the terminal, execute
```
sonar-scanner \
  -Dsonar.projectKey=sensemkaing \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9900 \
  -Dsonar.login=your_token_here
```
Go to [http://localhost:9900](http://localhost:9900)

## Stopping Sonarqube
In the terminal, execute
```
make down
```