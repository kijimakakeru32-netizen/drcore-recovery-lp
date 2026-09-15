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

店舗一覧カードには提供いただいた店内写真を使用しています（2枚目＝月島店、3枚目＝本八幡店）。カード全体から店舗ページへ移動できます。トップページでは店舗一覧を見ている間、追従予約ボタンを隠します。

月島店・本八幡店には、U18 open site.zipの「初回体験レッスンは60分から。」のCTAと金色のフローティングを移植しています。色・寸法・余白・光るアニメーションは元デザインに合わせ、文言は大人向けにしています。店舗ごとの予約リンクとクリック計測を引き継ぎ、フローティングはファーストビューを過ぎると表示されます。

両店舗のCTA・フローティングに、期限付きの体験1,000円を表示します。期限は日本時間の月末日22:00に翌月末へ切り替わります（例：9/30 21:59は「9/30まで」、22:00から「10/31まで」）。日付は閲覧時に計算するため、毎月の再公開は不要です。開いたままの場合も毎分更新し、画面復帰時にも再計算します。年越し・月の日数・うるう年を含め、`node --test tests/campaign-deadline.test.mjs` で検証できます。JavaScriptが無効の場合は、古い固定日付を出さず「期間限定」と表示します。

ロゴは `dist/assets/logo-transparent.svg` です。提供画像の輪郭をトレースした、透明背景のベクターSVGをヘッダーとフッターに使用しています。画像の埋め込みや描画時の透過フィルターを使わず、スマートフォンの高密度画面でも輪郭を直接描画します。更新時にはロゴURLに内容のハッシュを付け、古い画像キャッシュが残らないようにしています。元画像は `source-assets/logo-original.png` に保存しています。

## 編集

- `build.py`：店舗情報、予約URL、ヘッダー、店舗一覧、ページの生成
- `templates/`：3ページ共通の本文と料金
- `dist/assets/site.css`：レスポンシブのスタイル
- `dist/assets/base.css`：元LPと料金セクションのスタイル
- `dist/assets/site.js`：メニュー、FAQ以外の動作、クリック計測
- `templates/store-trial.html`・`templates/store-floating.html`・`dist/assets/store-cta.css`：店舗ページ専用のCTA
- `dist/assets/campaign-deadline.mjs`：日本時間で計算する月末22:00の期限更新

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
