# transform_speech
### 概要
文章を投げたら学習したキャラクターの言葉に変換するAPI
- 環境: 
  - anaconda3+nginx+uwsgi+mecab+cabocha  
- 環境構築方法は以下を参照:
  - https://m0t0k1ch1st0ry.com/blog/2016/07/30/nlp/ 
  - pyenvは使わないほうが良い

キャラクター発話変換方法は以下の論文を参考に組みました。  
`文章機能部の確率的書き換えによるキャラクタ性変換`: http://www.anlp.jp/proceedings/annual_meeting/2015/pdf_dir/B1-4.pdf

### API仕様
#### Transform API
- URI: `/transform`
- Method: `POST`
- リクエスト形式
  - header
  ```
  Content-Type:application/json
  ```
  - body
  ```
  {
      "sentence": [変換したい発話]
  }
  ```
- レスポンス形式
  - 200
  ```
  {
      "tranform_sentence": [変換された発話]
  }
  ```
  
- 例

```
$ curl localhost:80/transform -H "Content-Type:application/json" -d '{"sentence":"ロージアちゃんは可愛いですね"}' | jq
{
  "tranform_sentence": "ロージアちゃんは可愛いね"
}
```

### 学習データ
- ファイル形式: `csv`

```
from_sentence,to_sentence
[変換前発話],[変換後発話]
```
- 例:

```
from_sentence,to_sentence
そのことについて教えてください。,そのことについて教えてね。
```

### 設定ファイル
- 設定ファイルパス: `config/transform_config.json`
- 設定ファイル形式:

```
{
    "rule_table_path": [学習結果パス（これを使って推論を行う）],
    "teacher_data_path": [学習データパス（これを使って学習を行う）]
}
```
