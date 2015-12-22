import os
import subprocess

from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element

from abcscraper import AbstractScraper


class TgdbScraper(AbstractScraper):
    def __init__(self, addon_path):
        AbstractScraper.__init__(self, addon_path)
        self.api_url = 'http://thegamesdb.net/api/GetGame.php?name=%s'
        self.cover_cache = self._set_up_path(os.path.join(self.base_path, 'art/poster/'))
        self.fanart_cache = self._set_up_path(os.path.join(self.base_path, 'art/fanart/'))
        self.api_cache = os.path.join(self.base_path, 'api_cache/')

    def get_game_information(self, game_name):
        request_name = game_name.replace(" ", "+").replace(":", "")
        # TODO: This should return an instance of a specific response object
        return self._gather_information(request_name)

    def _gather_information(self, game):
        game_cover_path = self._set_up_path(os.path.join(self.cover_cache, game))
        game_fanart_path = self._set_up_path(os.path.join(self.fanart_cache, game))

        xml_response_file = self._get_xml_data(game)
        xml_root = ElementTree(file=xml_response_file).getroot()

        dict_response = self._parse_xml_to_dict(xml_root)
        if dict_response:
            dict_response['cover'] = self._dump_image(game_cover_path, dict_response.get('cover'))

            local_arts = []
            for art in dict_response.get('fanart'):
                local_arts.append(self._dump_image(game_fanart_path, art))
            dict_response['fanart'] = local_arts

            return dict_response

    def _get_xml_data(self, game):
        file_path = os.path.join(self.api_cache, game, '.xml')

        if not os.path.isfile(file_path):
            curl = subprocess.Popen(['curl', '-XGET', self.api_url % game], stdout=subprocess.PIPE)
            with open(file_path, 'w') as response_file:
                response_file.write(curl.stdout.read())

        return file_path

    @staticmethod
    def _parse_xml_to_dict(root):
        """

        :rtype: dict
        :type root: Element
        """
        data = {'year': 'N/A', 'plot': 'N/A', 'cover': 'N/A', 'genre': [], 'fanart': []}
        base_img_url = root.find('baseImgUrl')
        for game in root.findall('Game'):
            if game.find('Platform').text == 'PC':
                if game.find('ReleaseDate'):
                    data['year'] = os.path.basename(game.find('ReleaseDate').text)
                if game.find('Overview'):
                    data['plot'] = game.find('Overview').text
                for img in game.find('Images'):
                    if img.get('side') == 'front':
                        data['cover'] = os.path.join(base_img_url, img.text)
                    if img.tag == 'fanart':
                        data['fanart'].append(os.path.join(base_img_url, img.find('original').text))
                if game.find('Genres'):
                    for genre in game.find('Genres'):
                        data['genre'].append(genre.text)
                return data

        return None
