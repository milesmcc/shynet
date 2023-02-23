// This is a lightweight and privacy-friendly analytics script from Shynet, a self-hosted
// analytics tool. To give you full visibility into how your data is being monitored, this
// file is intentionally not minified or obfuscated. To learn more about Shynet (and to view
// its source code), visit <https://github.com/milesmcc/shynet>.
//
// This script only sends the current URL, the referrer URL, and the page load time. That's it!

{% if dnt %}
var Shynet = {
  dnt: true
};
{% else %}
var Shynet = {
  dnt: false,
  idempotency: null,
  heartbeatTaskId: null,
  skipHeartbeat: false,
  sendHeartbeat: function () {
    try {
      if (document.hidden || Shynet.skipHeartbeat) {
        return;
      }

      Shynet.skipHeartbeat = true;
      var xhr = new XMLHttpRequest();
      xhr.open(
        "POST",
        "{{protocol}}://{{request.get_host}}{{endpoint}}",
        true
      );
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.onload = function () { 
        Shynet.skipHeartbeat = false;
      };
      xhr.onerror = function () { 
        Shynet.skipHeartbeat = false;
      };
      xhr.send(
        JSON.stringify({
          idempotency: Shynet.idempotency,
          referrer: document.referrer,
          location: window.location.href,
          loadTime:
            window.performance.timing.domContentLoadedEventEnd -
            window.performance.timing.navigationStart,
        })
      );
    } catch (e) {}
  },
  newPageLoad: function () {
    if (Shynet.heartbeatTaskId != null) {
      clearInterval(Shynet.heartbeatTaskId);
    }
    Shynet.idempotency = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    Shynet.skipHeartbeat = false;
    Shynet.heartbeatTaskId = setInterval(Shynet.sendHeartbeat, parseInt("{{heartbeat_frequency}}"));
    Shynet.sendHeartbeat();
  }
};

window.addEventListener("load", Shynet.newPageLoad);
{% endif %}


{% if script_inject %}
// The following is script is not part of Shynet, and was instead
// provided by this site's administrator.
// 
// -- START --
{{script_inject|safe}}
// -- END --
{% endif %}
