from wiki import make_mw_request, get_wikitext, is_disambiguation_page
import settings

def test(title):
    settings.init()
    #print(get_wikitext(title))
    print(is_disambiguation_page(title))


if __name__ == '__main__':
    test('Ocalea')
    test('Cambridge_(disambiguation)')
    test('Cambridge')
    test('Soundex')
    test('Geographica')
    test('Pausanias')
    test('Idomene')