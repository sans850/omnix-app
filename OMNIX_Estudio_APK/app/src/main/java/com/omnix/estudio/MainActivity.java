package com.omnix.estudio;
import android.app.*; import android.content.*; import android.net.Uri; import android.os.*; import android.webkit.*; import android.widget.Toast;
public class MainActivity extends Activity {
  private WebView webView; private ValueCallback<Uri[]> cb;
  protected void onCreate(Bundle b) {
    super.onCreate(b); webView = new WebView(this); setContentView(webView);
    WebSettings ws = webView.getSettings(); ws.setJavaScriptEnabled(true); ws.setDomStorageEnabled(true); ws.setAllowFileAccess(true);
    CookieManager.getInstance().setAcceptCookie(true); webView.setWebViewClient(new WebViewClient());
    webView.setWebChromeClient(new WebChromeClient() {
      public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> c, FileChooserParams p) {
        cb = c; startActivityForResult(p.createIntent(), 1001); return true;
      }
    });
    webView.setDownloadListener((url, ua, cd, mime, len) -> {
      DownloadManager.Request r = new DownloadManager.Request(Uri.parse(url));
      String fn = URLUtil.guessFileName(url, cd, mime);
      r.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
      r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, fn);
      ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(r);
      Toast.makeText(this, "Baixando: " + fn, Toast.LENGTH_SHORT).show();
    });
    webView.loadUrl("https://setup-hardiness-sterilize.ngrok-free.dev/?modo=estudio");
  }
  protected void onActivityResult(int req, int res, Intent data) {
    if (req == 1001 && cb != null) { cb.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(res, data)); cb = null; }
  }
  public void onBackPressed() { if (webView.canGoBack()) webView.goBack(); else super.onBackPressed(); }
}
