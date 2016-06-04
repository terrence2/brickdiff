# brickdiff
Command line LEGO set and part management and optimization.

# Usage

> brickdiff init <bricklink credentials>
> brickdiff add --set 0001 --set 0002 ...etc...


# Credentials

The credentials file must be a json format file of the form:
`{
  "consumer": {
    "key": "______",
    "secret": "_______"
  },
  "access": {
    "key": "______",
    "secret": "_______"
  }
}`

