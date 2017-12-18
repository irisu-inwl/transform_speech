import pickle
import os

import CaboCha
import MeCab

wakati_tagger = MeCab.Tagger('-Owakati')

def save_pickle(file_path, data):
    if not file_path:
        return
    
    with open(file_path, mode='wb') as file:
        pickle.dump(data, file)

def load_pickle(file_path):
    if not (file_path and os.path.isfile(file_path)):
        return []

    with open(file_path, mode='rb') as file:
        return pickle.load(file)

def get_wakati(sentence):
    return wakati_tagger.parse(sentence).split(' ')[:-1]

def get_pos_feature(tree, chunk):
    """
    return:
        (主単語,主単語の基本形,品詞)
    """
    surface = ''
    base_surface = ''
    pos = ''
    for i in range(chunk.token_pos, chunk.token_pos + chunk.token_size):
        token = tree.token(i)
        features = token.feature.split(',')
        if features[0] == '名詞':
            if token.surface == '♥': continue
            pos = features[0]
            surface += token.surface
            base_surface += token.surface
        elif features[0] == '形容詞':
            pos = features[0]
            surface += token.surface 
            base_surface += features[6]
            break
        elif features[0] == '動詞':
            pos = features[0]
            surface += token.surface 
            base_surface += features[6]
            break
    return surface,base_surface,pos

def validation_transform(from_sentence, to_sentence):
    """
    対象変換の係り受け構造が同値かを判断する
    """
    # 同じパーサで解析するとparse結果が同じになってしまう
    cp = CaboCha.Parser('-f1')
    cp2 = CaboCha.Parser('-f1')

    from_tree = cp.parse(from_sentence)
    to_tree = cp2.parse(to_sentence)
    # if from_tree.size() != to_tree.size(): return False
    if from_tree.chunk_size() != to_tree.chunk_size(): return False
    from_chunks = [from_tree.token(i).chunk for i in range(0, from_tree.size()) if from_tree.token(i).chunk]
    to_chunks = [to_tree.token(i).chunk for i in range(0, to_tree.size()) if to_tree.token(i).chunk]
    for from_chunk, to_chunk in zip(from_chunks,to_chunks):
        if from_chunk.link != to_chunk.link:
            return False

    return True

def get_words_received_relates(line):
    """
    return:
        {
            'chunks': [{
                'chunk': cabochaから得られたchunkオブジェクト,
                'surface': その文節の主となる単語（品詞が名詞、形容詞、動詞となるもの）,
                'base_surface': 主単語の基本形,
                'pos': 主単語の品詞,
                'phrase': 文節リスト（わかち書きでリスト化したもの）,
                'related_spieces': 係り受け種別
            }],
            'tuples': 単語同士の関係タプル構造
        }
    """
    cp = CaboCha.Parser('-f1')
    tree = cp.parse(line)
    word_list = wakati_tagger.parse(line).split(' ')
    word_list = word_list[:-1] # 最後に\nが入るので除く
    chunk_dic = {'chunks':[]}
    chunk_list_dic = {} # 文節のリストの辞書
    chunk_id = -1

    for i in range(0, tree.size()):
        token = tree.token(i)
        if token.chunk:
            chunk_id += 1
            surface, base_surface, pos = get_pos_feature(tree, token.chunk)
            chunk_obj = {'chunk': token.chunk, 
                        'surface': surface,
                        'base_surface': base_surface,
                        'pos': pos}
            chunk_dic['chunks'].append(chunk_obj)

        # chunk_list_dicに要素を代入
        if max(chunk_id,0) < len(chunk_list_dic):
            chunk_list_dic[max(chunk_id,0)].append(word_list[i])
        else:
            chunk_list_dic[max(chunk_id,0)] = [word_list[i]]

    tuples = []
    for chunk_id,chunk_obj in enumerate(chunk_dic['chunks']):
        # いい機会だし文節を一つの辞書にまとめる
        chunk_obj['phrase'] = chunk_list_dic[chunk_id]
        if chunk_obj['chunk'].link > 0:
            # 係り種別の決定と単語間の係り構造を抽出
            from_surface = chunk_obj['base_surface']
            to_surface = chunk_dic['chunks'][chunk_obj['chunk'].link]['base_surface']
            tuples.append((from_surface, to_surface))
            if '名詞' == chunk_dic['chunks'][chunk_obj['chunk'].link]['pos']:
                chunk_obj['related_spieces'] = '連体'
            else:
                chunk_obj['related_spieces'] = '連用'
        else:
            # 係り種別が文末
            if '？' in chunk_obj['phrase']:
                chunk_obj['related_spieces'] = '文末-疑問'
            else:
                chunk_obj['related_spieces'] = '文末-平叙'

    chunk_dic['tuples'] = tuples
    # debug print
    # print( chunk_dic )
    return chunk_dic