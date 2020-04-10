window.onload = function () {
  var idempotency =
    Math.random().toString(36).substring(2, 15) +
    Math.random().toString(36).substring(2, 15);
  function sendUpdate() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "{{endpoint}}", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(
      JSON.stringify({
        idempotency: idempotency,
        referrer: document.referrer,
        loadTime:
          window.performance.timing.domContentLoadedEventEnd -
          window.performance.timing.navigationStart,
        hitMetadata:
          typeof shynetHitMetadata !== "undefined" ? shynetHitMetadata : {},
        sessionMetadata:
          typeof shynetSessionMetadata !== "undefined"
            ? shynetSessionMetadata
            : {},
      })
    );
  }
  setInterval(sendUpdate, 5000);
  sendUpdate();
};
