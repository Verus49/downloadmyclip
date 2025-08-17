const BACKEND_URL = "https://REPLACE_WITH_YOUR_DOMAIN/upload_cookies";

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.url) return;
  let domain;
  if (tab.url.includes("tiktok.com")) domain = "tiktok.com";
  else if (tab.url.includes("youtube.com")) domain = "youtube.com";
  else if (tab.url.includes("instagram.com")) domain = "instagram.com";
  else if (tab.url.includes("facebook.com")) domain = "facebook.com";
  else {
    alert("This site is not supported.");
    return;
  }

  chrome.cookies.getAll({ domain }, async (cookies) => {
    if (!cookies.length) {
      alert("No cookies found for " + domain);
      return;
    }

    let cookieText = cookies.map(c => {
      return [
        "TRUE",
        c.domain,
        "TRUE",
        c.path,
        c.secure ? "TRUE" : "FALSE",
        Math.floor((c.expirationDate || (Date.now()/1000+3600))),
        c.name,
        c.value
      ].join("\t");
    }).join("\n");

    try {
      await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ site: domain, cookies: cookieText })
      });
      alert("✅ Cookies sent to DownloadMyClip for " + domain);
    } catch (err) {
      console.error(err);
      alert("❌ Failed to send cookies.");
    }
  });
});