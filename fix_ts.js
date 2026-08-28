const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, 'scripts', 'validate_typescript_syntax.js');
let code = fs.readFileSync(file, 'utf8');
code = code.replace('ts.ScriptTarget.Latest', 'ts.ScriptTarget.ESNext');
fs.writeFileSync(file, code);
