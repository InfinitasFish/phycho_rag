### 1. Работа с данными

#### Шишаев Вячеслав:
- С помощью speech-recognition модели Whisper транскрибировал видео психолога Alok Kanojia, aka HealthyGamerGG (https://www.healthygamer.gg/dr-alok-kanojia). После ручной фильтрации были собраны тексты 63-х видео, хронометражем от 20 минут до полутора часа. Фишка данных заключается в том, что этот психолог в дружественной манере рассказывает о новых и актуальных проблемах, с которыми сталкиваются люди в эпоху интернета.
#### Тихановский Дмитрий:
- Был скачен раздел психологических книг с портала флибуста (3000 книжек) и приведен к формату pdf

    1. **`load.py`**: Автоматически скачивает книги из категории психологии, используя Selenium, и сохраняет их в предпочтительных форматах (FB2, EPUB, MOBI).
    
    3. **`unzip.py`**: Распаковывает ZIP-архивы с книгами и удаляет их после извлечения.

    2. **`transform.py`**: Преобразует книги в PDF, исправляя ошибки форматов и удаляя исходные файлы после конвертации.


#### Горохова Александра:
- Был спаршен журнал [zigmund.online](https://zigmund.online/journal/) со статьями по психологии и краткими советами по борьбе с психологическими проблемами. Все статьи скачаны в формате json

    1. **`parse_zigmund.py`**: Получает все ссылки на статьи с главной страницы журнала, а затем парсит текста статей и приводит их к формату json.