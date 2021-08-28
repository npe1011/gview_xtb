# WindowsのGaussViewからXTB最適化をできるようにする

実験化学系、特に有機化学系で計算もやってるという人たち（含む自分自身）は、Gaussianを使ってる人が圧倒的に多く、可視化や構造の編集についてWindowsのGaussViewを使ってる人がかなり多いと思います（偏見）。
そこでGaussViewからワンクリックでXTB最適化が走るようなセットアップを立てました。

## 1. ソフトウェアのバージョン
G16W と GaussView6 でやっていますが、多分よほど古くなければ動くと思います。GaussViewからG16Wを呼び出し、そこからXTBを呼ぶ形なのでG16Wも必須です。

## 2. XTBの準備
https://github.com/npe1011/xtb_windows_build に従って準備します。

## 3. Gaussian の external interface について
Gaussian は外部のプログラムにエネルギーと勾配、Hessianを計算させて構造最適化等をすることができます。そもそもはONIOMなどで使うように想定されてますが、別に普通の計算に使うこともできます。インプットの行に `external='exec_file'` とすると、Gaussian は exex_file を各ステップごとに実行して、エネルギーやその微分を計算させます。exec_file は実行可能で、所定のフォーマットのファイルを受け取り、所定のフォーマットのファイルを出力することを要求されますので、適当なプログラムやスクリプトでXTBとやりとりすればOKです。

## 4. Gaussian/XTB interface

`gau2xtb.py` はそのinterfaceです。このままだとPython環境が必要かつ実行時の指定がめんどくさい（`external=gau2xtb` でうまく走らない）ので、Pyinstaller [https://www.pyinstaller.org/] で実行可能形式にしました。`python -m pip install pyinstaller` したあと、 `pyinstaller gau2xtb.py --onefile` として `gau2xtb.exe` を作成しました。[https://github.com/npe1011/gview_xtb/releases/tag/v1.0] においてあります。

## 5. 準備
`gau2xtb.exe` は PATH が通った場所に置く必要があります。また xtb も `xtb` コマンドだけで実行できる必要があるので、 [https://github.com/npe1011/xtb_windows_build] で xtb を入れたフォルダに `xtb.bat` と `gau2.xtb` を置き、そこに PATH を通します。 フォルダ構成は下記のような感じで、この `xtb-6.4.1` フォルダを 環境変数 PATH 追加します。
```
xtb-6.4.1/
  ├ bin/
　├ include/
　├ share/
  ├ share/
  ├ lib/
  ├ xtb.bat
　└ gau2xtb.exe
```

## 6. GaussView の Calculation Schemes の追加
上記の準備が出来た状態で、GaussianからXTBでOPTするには下記のようなインプットになります。 `opt=nomicro` が必要なことに注意。

```
# p opt=nomicro external='gau2xtb'

title

0 1
C 0.00 0.00 0.00
H 1.00 0.00 0.00
...

これを毎回書いているようでは手間なので、GaussViewに設定を追加します。GaussViewから計算することは普段めったにないかもしれませんが、Calculation Schemesみたいなよく使う設定を用意しておいて、計算を簡単にする機能があります。GaussView の 下図の辺りです。

![gv](https://user-images.githubusercontent.com/85745743/131203497-1c9c5659-6e09-43b4-98e8-1df6da1b0516.png)

適当な分子を書いたあと、編集 (Gaussian Calculations Schemes Dialog) を開いて、出てきたダイアログで、右クリック-> Open File -> Merge を選択して、xtbopt.txt を読み込みます。
ダイアログを閉じると隣の選択ボックスから xtbopt が選択できます。これを選んで、Quich Launch を押せば構造最適化が実行されます。

## 7. 問題点
遅い…… いちいち Gaussianとやりとりをして、Gaussian側 が最適化計算をやってるので 素でxtb計算やるよりめちゃくちゃ遅いですね。
pyinstaller で exe にするときに `--onefile` にしないとちょっとマシかもですが、焼け石に水でしょう……
まあXTB計算部分は十二分に速いので、系が小さくても大きくてもあまり変わらないとは思います。


## 8. その他
上記の gau2xtb.exe ですが、`external='gau2xtb'' をいじればコマンドラインオプションも渡せますので、溶媒やらなにやらを設定することもできます。

```
#p opt=nomicro external='gau2xtb --gbsa CH2Cl2'
```

何も指定しないとXTBのデフォルトで計算します。
