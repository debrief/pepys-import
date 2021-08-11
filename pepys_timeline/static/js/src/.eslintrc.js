module.exports = {
  "env": {
    "browser": true,
    "commonjs": true,
    "es6": true,
    "jquery": true
  },
  "parserOptions": {
    "ecmaVersion": 11,
  },
  "extends": 'eslint:recommended',
  "rules": {
	"no-console": 0,
  },
  "globals": {
    "moment": "readonly",
    "easytimer": "readonly",
    "visavail": "readonly",
    "getParticipantIconUrl": "readonly",
  }
}