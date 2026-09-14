# Dr.core 大人向けLP

添付の大人向けLPの写真・本文・スタイルを活用した、本番用の静的サイトです。

| ページ | 公開パス |
| --- | --- |
| トップ・店舗一覧 | `/` |
| 月島店 | `/gyms/tsukishima/` |
| 本八幡店 | `/gyms/motoyawata/` |

トップの予約ボタンはSHOP LISTへ移動し、店舗ページの予約ボタンは指定された各店舗の予約ページを別タブで開きます。予約の確定操作は外部の予約サイトで行います。

料金はU18 open site.zipの料金セクションから移植。初回体験、月額プラン、当日入会の永続割引、入会金、ペア割引を共通化しています。体験内容と写真は大人向けに調整し、無料レンタルウェアを掲載しています。

月島店の店舗データは公式ページ https://drcore.jp/gyms/tsukishima/ を参照。本八幡店は添付資料の住所・営業時間10:00〜21:00・定休日なしを使用しています。本八幡店の電話番号は資料に記載がなく掲載していません。

店舗一覧カードには提供いただいた店内写真を使用しています（2枚目＝月島店、3枚目＝本八幡店）。カード全体から店舗ページへ移動できます。店舗一覧を見ている間は追従予約ボタンを隠し、カードの内容を遮らないようにしています。

ロゴは `dist/assets/logo-transparent.svg` です。提供された白いロゴ画像を内部に保持し、SVGのフィルターで背景色だけを透明にします。ロゴの文字形・字間は元画像のままで、ヘッダーとフッターの両方に使用しています。元画像は `source-assets/logo-original.png` に保存しています。

## 編集

- `build.py`：店舗情報、予約URL、ヘッダー、店舗一覧、ページの生成
- `templates/`：3ページ共通の本文と料金
- `dist/assets/site.css`：レスポンシブのスタイル
- `dist/assets/base.css`：元LPと料金セクションのスタイル
- `dist/assets/site.js`：メニュー、FAQ以外の動作、クリック計測

`python3 build.py --full --origin https://公開先のドメイン` で3ページとサイトマップを生成します。公開先を変更する場合は、このコマンドでcanonical・OG情報・サイトマップも更新してください。実際に配信するファイルは `dist/` の中身です。既存のdrcore.jpは変更していません。

`python3 verify.py` と `node --check dist/assets/site.js` で静的検証できます。スマートフォン390px・PC1440pxで表示、メニュー、FAQ、店舗遷移、追従CTAを確認済みです。

## 計測

元資料のGTM（GTM-TJ8DFDN6）とClarityを引き継いでいます。予約クリックは `reserve_click`、店舗選択は `store_select` です。`program: 大人`、`store`、`position`、`destination` をdataLayerに送ります。外部予約の完了計測は予約システム側の設定に依存します。

## Netlifyでの公開

- 公開サイト：https://drcore-adult-lp.netlify.app/
- GitHub：https://github.com/kijimakakeru32-netizen/drcore-adult-lp （非公開リポジトリ）
- Netlify管理画面：https://app.netlify.com/projects/drcore-adult-lp

GitHubの `main` ブランチをNetlifyに連携し、pushするたびに3ページを生成・検証して公開します。設定は `netlify.toml` にまとめてあります。公開ディレクトリは `dist` です。ビルド時にNetlifyの `URL` 環境変数を使い、canonical、OG情報、サイトマップを公開先のドメインにそろえます。

Python標準ライブラリで生成するため、外部パッケージのインストールは不要です。ソースは `build.py` と `templates/`、画像やCSSは `dist/assets/` を編集してください。生成済みHTMLは次のビルドで上書きされます。
