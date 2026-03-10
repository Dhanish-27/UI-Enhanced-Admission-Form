import re

file_path = r'e:\Django\Admission-Form-main\admission\templates\staff\admissions_inline.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

def fix_operators(match):
    text = match.group(0)
    # Fix '!='
    text = re.sub(r'(?<! )!=(?! )', ' != ', text)
    text = re.sub(r"!='", " != '", text)
    text = re.sub(r"'!=", "' != ", text)
    # Re-collapse multiple spaces
    text = re.sub(r' \s*!=\s* ', ' != ', text)
    
    # Fix '=='
    text = re.sub(r'(?<! )==(?!=)(?! )', ' == ', text)
    text = re.sub(r'==', ' == ', text)
    text = re.sub(r' \s*==\s* ', ' == ', text)
    text = re.sub(r"=='", " == '", text)
    
    # Let's just fix the specific issue the compiler complained about
    return text

content = re.sub(r'\{%.*?%\}', fix_operators, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Operators fixed")
