import re

file_path = r'e:\Django\Admission-Form-main\admission\templates\staff\admissions_inline.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

def fix_equals(match):
    text = match.group(0)
    text = re.sub(r'(?<! )==(?!=)(?! )', ' == ', text)
    text = re.sub(r'==', ' == ', text)
    text = re.sub(r' \s*==\s* ', ' == ', text)
    # also handle '==' to ' == '
    text = re.sub(r"=='", " == '", text)
    return text

content = re.sub(r'\{%.*?%\}', fix_equals, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Equals fixed")
