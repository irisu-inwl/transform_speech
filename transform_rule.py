import re
import json
import csv
import sys

import util

# wakati_tagger = MeCab.Tagger('-Owakati -d /usr/lib64/mecab/dic/mecab-ipadic-neologd')

class Transform_Rule:
    from_fpp = {'オイラ', '吾輩', 'あたい', 'ボク', 'あたし', '私', 'おら', 'こちら', 'オレ', 'わがはい', 'わし', 'ぼく', '小生', 'われわれ', '余', 'わい', '僕', 'わたくし', '我々', 'おれ', 'おいら', 'あちき', '俺', 'わたし', 'われ'}
    from_spp = {'あなた', 'わい', 'キミ', 'きみ', 'おのれ', 'あんた', 'お前', '君', 'てめぇ', 'そち'}
    def __init__(self, config_path='./data/transform_config.json'):
        self._rule_table = []
        config = {}

        self.to_fpp = 'ロージアちゃん'
        self.to_spp = 'お兄ちゃん'

        with open(config_path,'r') as file:
            config = json.load(file)
        
        self._rule_table_path = config.get('rule_table_path')
        self._teacher_data_path = config.get('teacher_data_path')
        self._rule_table = util.load_pickle(self._rule_table_path)     

    def put_rule_table(self):
        """
        rule_tableを新しく作成し、保存。
        """
        self._rule_table = []
        self.create_rule_table()
        self.save_table()

    def optional_learning(self, file_path=''):
        """
        指定したpathで追加学習
        """
        self.create_rule_table(file_path)
        self.save_table()

    def save_table(self):
        """
        rule_tableをpickle.dumpで保存する
        """
        util.save_pickle(self._rule_table_path, self._rule_table)
    
    def search_table(self, related_spieces='', pos='', from_word='', to_word=''):
        """
        指定した条件で検索する
        """
        search_query = [('related_spieces',related_spieces), ('pos',pos), ('from_word',from_word), ('to_word',to_word)]
        return list(filter(lambda x:all(val in x[key] for key,val in search_query), self._rule_table))

    def add_heart_symbol(self, sentence):
        """
        とりあえず、愚直に'。'を'♥'にする
        TODO: 文書の特徴量（文節数や終端語の品詞）から2値分類で♥を作る
        """
        return re.sub('。', '♥', sentence)

    def transform_personal_pronounce(self, sentence):
        """
        人称代名詞の変換メソッド。今は愚直に形態素で人称代名詞辞書から見つかったものを変換する
        """
        sentence_list = []
        wakati_list = util.get_wakati(sentence)
        for phrase in wakati_list:
            if phrase in Transform_Rule.from_fpp:
                phrase = self.to_fpp
            if phrase in Transform_Rule.from_spp:
                phrase = self.to_spp
            sentence_list.append(phrase)

        return ''.join(sentence_list)

    def fit_rule_table(self, target_sentence):
        """
        入力した発話を変換ルールでキャラクター発話ssssへと変換
        """
        chunk_dic = util.get_words_received_relates(target_sentence)
        sentence_list = []
        for chunk_obj in chunk_dic['chunks']:
            related_spieces = chunk_obj['related_spieces']
            pos = chunk_obj['pos']
            from_word = ''
            sub_table = self.search_table(related_spieces=related_spieces, pos=pos)
            search_table = []
            sentence = ''.join(chunk_obj['phrase'])
            # まず、対象となる文節の係り種と品詞でフィルターし、その中でfrom_sentenceを探す
            for record in sub_table:
                if record['from_word'] in sentence:
                    # 検索した単語が後ろの単語かのチェックが必要
                    # if sentence.index(record['from_word'])+len(record['from_word']) != len(sentence): continue
                    if len(record['from_word']) < len(from_word): continue
                    from_word = record['from_word']
                    search_table = self.search_table(related_spieces=related_spieces, pos=pos,from_word=from_word)
                    if search_table:
                        break

            if not search_table:
                sentence_list.append(sentence)
                continue
            
            max_table = max(search_table, key=(lambda x:x['count']))
            sentence = re.sub(max_table['from_word'], max_table['to_word'], sentence)
            sentence_list.append(sentence)

        return_sentence = ''.join(sentence_list)

        # 後ろにハートをつける
        return_sentence = self.add_heart_symbol(return_sentence)
        # 人称代名詞の変換
        return_sentence = self.transform_personal_pronounce(return_sentence)

        return return_sentence

    def create_rule_table(self,file_path=''):
        """
        configで読み込んだ教師データからrule_tableを作成する
        """
        if not file_path: file_path = self._teacher_data_path
        with open(file_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                self.put_transform_rule(row['from_sentence'], row['to_sentence'])

    def _create_rule(self, from_chunk_obj, to_chunk_obj):
        """
        Returns:
            {
                'related_spieces': {[係り種別],
                'pos': [主単語の品詞], 
                'from_word': [元の単語],
                'to_word': [変換先の単語],
                'count': [カウント数],
                'from_word_back': [from_wordの一語後ろ] # koreha...
           }
        """

        return_structure = {
            'related_spieces' : from_chunk_obj['related_spieces'],
            'pos' : from_chunk_obj['pos']
        }

        from_phrase = ''.join(from_chunk_obj['phrase'])
        to_phrase = ''.join(to_chunk_obj['phrase'])

        from_idx = from_phrase.index(from_chunk_obj['surface'])
        to_idx = to_phrase.index(to_chunk_obj['surface'])
        from_word = from_phrase[from_idx:]
        to_word = to_phrase[to_idx:]

        # 文節の語尾変化抽出処理
        # 単語の変化点を見つける
        word_idx = min(len(from_word),len(to_word))
        for idx in range(0, min(len(from_word),len(to_word))):
            if from_word[idx] != to_word[idx]:
                word_idx = idx
                break

        from_surface_len = len(from_chunk_obj['surface'])
        to_surface_len = len(to_chunk_obj['surface'])
        if from_word[word_idx:] or to_word[word_idx:]:
            # 変化点が存在すれば、それを採用する
            from_surface_len = word_idx
            to_surface_len = word_idx

        return_structure['from_word'] = from_word[from_surface_len:]
        return_structure['to_word'] = to_word[to_surface_len:]
        if from_surface_len != 0:
            return_structure['from_word_back'] = from_word[from_surface_len-1]

        if not return_structure['from_word']:
            return None
        return_structure['count'] = 1
        return return_structure

    def put_transform_rule(self, from_sentence, to_sentence):
        """
        与えられた語変換から変換規則テーブルを更新する
        """
        # debug
        # print( 'transform rule create::\n input from_sentence: {0} \n input to_sentence: {1}'.format(from_sentence, to_sentence) )
        if not util.validation_transform(from_sentence, to_sentence):
            sys.stderr.write('Transform isnt equal to:\nfrom: {0}\nto: {1}\n'.format(from_sentence,to_sentence))
            return
        from_chunk_dic = util.get_words_received_relates(from_sentence)
        to_chunk_dic = util.get_words_received_relates(to_sentence)

        # 分節ごとに変換テーブルを作成する
        for from_chunk_obj, to_chunk_obj in zip(from_chunk_dic['chunks'], to_chunk_dic['chunks']):
            rule = self._create_rule(from_chunk_obj, to_chunk_obj)
            # 無かったら次へ
            if not rule: continue

            phrase_table = None

            # それまでの変換規則で既存のものはあるかを検索
            for table in self._rule_table:
                if all((k,v) in rule.items() for (k,v) in table.items() if k != 'count'):
                    phrase_table = table

            # 存在するかしないかで更新するか新規作成するかの処理
            if phrase_table:
                phrase_table['count'] += 1
            else:
                self._rule_table.append(rule)

if __name__ == '__main__' :
    line = 'そういえば思い出したんですけど、宝石を測るカラットって単位は、重量を意味してるらしいですよ。'
    # line = 'ロージアちゃんはお兄ちゃんの事が好きだ'
    # get_transform_rule('最近きになるニュースとかあります？','最近きになるニュースとかある？')
    tr = Transform_Rule()
    # tr.put_rule_table()
    # print(tr._rule_table)
    print('input: %s' % line)
    print('rule fitting: %s' % tr.fit_rule_table(line))
