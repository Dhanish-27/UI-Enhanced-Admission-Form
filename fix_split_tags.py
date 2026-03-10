import re

file_path = r'e:\Django\Admission-Form-main\admission\templates\staff\admissions_inline.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix split tags
content = re.sub(r'\{%\s*if\s+([^%]+?)\s*%\}', lambda m: '{% if ' + m.group(1).replace('\n', ' ').strip() + ' %}', content)
content = re.sub(r'\{%\s*elif\s+([^%]+?)\s*%\}', lambda m: '{% elif ' + m.group(1).replace('\n', ' ').strip() + ' %}', content)
# fix {% endif %}
content = re.sub(r'\{%\s*endif\s*%\}', '{% endif %}', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Tags fixed")
