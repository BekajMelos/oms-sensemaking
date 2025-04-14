# Pull Request

* Closes #[PROVIDE ISSUE NUMBER HERE]

## Changes

Add a description of your merge request here.


## Test Procedure
Mention if there are new dependencies or resources needed to verify this branch.

* checkout this branch
* Run `source .venv/bin/activate`
* Copy updates from `.env.template` to `.env`
* Run `pip install -e ".[dev,docs,test,build]"`
* Run `make up`
* Run `make fix`, verify no changes
* Run `make test`, verify no failures
* Add additional testing steps here...

## Checklist before requesting a review
- [ ] I have performed a self-review of my code
- [ ] If it is a core feature, I have added thorough tests.
- [ ] I have opened or added changes to an MR for Sensemaking in the omsb-helm-charts repo
- [ ] I have updated environment variables in the docs
- [ ] I've updated the changelog
