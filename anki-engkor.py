import sqlite3
import genanki
from xml.etree import ElementTree
import unicodedata
import argparse
import random

ANKI_MODEL_ID = random.randrange(1 << 30, 1 << 31)
ANKI_DECK_ID = random.randrange(1 << 30, 1 << 31)

def collate_noaccent(string1, string2):
  norm_string1 = unicodedata.normalize('NFKD', string1).encode('ASCII', 'ignore')
  norm_string2 = unicodedata.normalize('NFKD', string2).encode('ASCII', 'ignore')

  if norm_string1 == norm_string2:
    return 0
  elif norm_string1 < norm_string2:
    return 1
  else:
    return -1

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Anki Deck Creator from English-Korean Dictionary')
  parser.add_argument('--list', required=True, help='Word list text file separated by newline')
  parser.add_argument('--name', required=True, help='Name of Anki deck')
  parser.add_argument('--output', required=True, help='File path of .apkg output')

  args = parser.parse_args()

  with open('style.css') as f:
    css = f.read()

  dict_model = genanki.Model(
    ANKI_MODEL_ID,
    'Dictionary Model',
    fields=[
      {'name': 'Word'},
      {'name': 'Definition'},
    ],
    css=css,
    templates=[
      {
        'name': 'Card 1',
        'qfmt': '<div class="word">{{Word}}</div>',
        'afmt': '{{FrontSide}}<hr id="answer"><div class="definition">{{Definition}}</div>',
      },
    ])

  conn = sqlite3.connect('koreng-dictionary.db')
  conn.create_collation('NOACCENT', collate_noaccent)

  deck = genanki.Deck(ANKI_DECK_ID, args.name)

  with open(args.list) as f:
    for line in f:
      word = line.strip()
      cursor = conn.execute('SELECT * FROM definitions WHERE title=?', (word, ))
      row = cursor.fetchone()
      if row is None:
        cursor = conn.execute('SELECT * FROM definitions WHERE title=? COLLATE NOACCENT', (word, ))
        row = cursor.fetchone()
      if row is None:
        print('== Word %s doesn\'t exist.' % word)
        continue
      xml = row[2].decode('utf-8')
      root = ElementTree.fromstring(xml)
      html = ''
      for child in root:
        html += ElementTree.tostring(child, encoding='unicode')

      note = genanki.Note(model=dict_model, fields=[word, html])
      deck.add_note(note)

  print('\n== Done!')

  genanki.Package(deck).write_to_file(args.output)
