//
// (c) 2026 Yoichi Tanibayashi
// 開発用の live reload（webapp --debug のときだけ読み込まれる）
//
// サーバーは繋がるだけの WebSocket を出しているだけで、何も送ってこない。
// **切断そのものが「再起動が始まった」の合図**で、繋ぎ直せるようになった
// 時点で再読み込みする。サーバー側にファイル監視のロジックは要らない。
//
"use strict";

(function () {
  const RETRY_MS = 400;

  const url = (location.protocol === "https:" ? "wss://" : "ws://")
    + location.host + window.URL_PREFIX + "/livereload";

  /* サーバーが復活するまで繋ぎ直し、繋がったら再読み込みする */
  function reloadWhenBack() {
    const timer = setInterval(() => {
      const probe = new WebSocket(url);

      probe.onopen = () => {
        clearInterval(timer);
        probe.close();
        location.reload();
      };
      // 再起動中は当然つながらない。コンソールにエラーが出るが実害は無い
      probe.onerror = () => probe.close();
    }, RETRY_MS);
  }

  function connect() {
    const socket = new WebSocket(url);

    socket.onopen = () => console.log("[livereload] 待機中");
    socket.onclose = () => {
      console.log("[livereload] 切断。サーバーの復帰を待ちます");
      reloadWhenBack();
    };
  }

  connect();
})();
