# TODO-052. 移調の候補を、音符と音の長さの合計で並べる

## きっかけ

並び順が**音符の数だけ**（`-c['notes']`）だった。音の長さは表に出して
いるのに順位に効かないので、「上の行のほうが音の長さは短い」が普通に
起きる。表を上から読む人にとっては、順位の根拠が見えない。

## やったこと

- `transpose.py` に `transpose_rank_key()` を作った。**`note_pct + sec_pct`
  の大きい順**。どちらも分母が曲全体なので、そのまま足して比べられる
- `transpose_candidates()` / `add_transpose_rows()` /
  `select_transpose_rows()` の並べ替えを、すべてこれに寄せた。
  **`key=` を 3 か所に持たない**（片方だけ直して食い違うのを避ける）
- 同じ調の中でどのオクターブを残すか（`best_of_key`）も同じ物差しにした。
  かつては `(notes, -|t|)` の比較で、並べ替えとは別の式だった
- 同点の決まりは変えない（調を変えない案が上 → 移調量が小さい順）
- **`transpose_notices()` の「音符の 1 位」を数え直すようにした。**
  `candidates[0]` は合計の 1 位であって、音符の 1 位とは限らなくなった。
  そのまま使うと「音符の数では 調+3」が嘘になる

## テスト

`tests/test_rollbook.py`

- `test_transpose_rank_key_uses_both_metrics` — 音符が少なくても、
  長さで大きく勝てば上に来る
- `test_transpose_rank_key_tie_prefers_the_same_key` — 同点のときの
  決まりは従来どおり
- `test_transpose_candidates_are_sorted_by_total_score` — 並びが
  2 つの合計の降順になっている
