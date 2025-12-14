import random
import string

print('Welcome to Word List Generator!')
# Created by roshan choudhury
first_name = input('Enter victim first name: ').lower()
last_name = input('Enter victim last name: ').lower()
dob = input('Enter victim date of birth (DD/MM/YYYY): ').lower()
anniversary = input('Enter victim anniversary (DD/MM/YYYY): ').lower()
pet_name = input('Enter victim pet name (optional, press Enter to skip): ').lower()
favorite_number = input('Enter victim favorite number (optional, press Enter to skip): ').lower()
is_smart = input('Is victim smart? (yes/no): ').lower()

# Leetspeak replacements if smart
leetspeak = {'a': '@', 's': random.choice(['&', '$']), 'e': '3', 'i': '1', 'o': '0'}

def apply_leetspeak(word):
    if is_smart == 'yes':
        return ''.join(leetspeak.get(c, c) for c in word)
    return word

def random_case(word):
    return ''.join(random.choice([c.upper(), c.lower()]) for c in word)

# Ask for number of passwords, default to 1000
try:
    num_passwords = int(input('How many passwords to generate? (press Enter for 1000): ') or 1000)
except ValueError:
    num_passwords = 1000

# Generate word list
word_list = []
base_names = [first_name, last_name, first_name + last_name, last_name + first_name]
extras = [dob, anniversary, pet_name, favorite_number]
extras = [e for e in extras if e]  # Remove empty extras

for base in base_names:
    leet_base = apply_leetspeak(base)
    word_list.append(leet_base)
    word_list.append(leet_base.capitalize())
    word_list.append(random_case(leet_base))  # Add random case variation
    # Add extras
    for extra in extras:
        word_list.append(leet_base + extra)
        word_list.append(extra + leet_base)
        word_list.append(random_case(leet_base + extra))  # Random case
    # Add numbers
    for num in ['123', '2023', '99']:
        word_list.append(leet_base + num)
        word_list.append(num + leet_base)
        word_list.append(random_case(leet_base + num))
    # Add symbols
    for sym in ['!', '@', '#']:
        word_list.append(leet_base + sym)
        word_list.append(random_case(leet_base + sym))
    # Random variations
    for _ in range(5):
        random_name = ''.join(random.choice(string.ascii_letters) for _ in range(len(base)))
        word_list.append(apply_leetspeak(random_name))
        word_list.append(random_case(apply_leetspeak(random_name)))

# Remove duplicates and limit to num_passwords
word_list = list(set(word_list))[:num_passwords]

# Save to txt file
with open('generated_wordlist.txt', 'w') as f:
    for word in word_list:
        f.write(word + '\n')


print(f'Generated {len(word_list)} words and saved to generated_wordlist.txt')
