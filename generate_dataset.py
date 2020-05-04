from wiki import get_random_pages, get_interlang_titles, request_links
import settings

settings.init('zh', False)
languages = ['en', 'de', 'es' ]

count = 0
while count < 100:
    en_page_titles = get_random_pages(500)

    for title in en_page_titles:
        links, plcontinue = request_links(title)
        if len(links) <= 10:
            interlang_titles = get_interlang_titles(title, languages)

            add_to_ds = True
            for lang in languages:
                if lang not in interlang_titles:
                    add_to_ds = False
                    break
            
            if add_to_ds:
                with open('wikipedia_dataset/titles_zh.txt', 'a') as fw:
                    fw.write('{0}\n'.format(title))
                
                for lang in languages:
                    with open('wikipedia_dataset/titles_{0}.txt'.format(lang), 'a') as fw:
                        fw.write('{0}\n'.format(interlang_titles[lang]))

                #print(f'{title}, {interlang_titles["es"]}, {interlang_titles["de"]}, {interlang_titles["en"]}')
                count += 1
