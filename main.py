import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),"lib"))
import json
from flask import Flask, request, make_response, jsonify, send_file
app = Flask(__name__)
app.config['DEBUG'] = True

import youtube_dl


class SimpleYDL(youtube_dl.YoutubeDL):
	def __init__(self, *args, **kargs):
		super(SimpleYDL, self).__init__(*args, **kargs)
		self.add_default_info_extractors()


def get_videos(url):    
	'''
	Get a list with a dict for every video founded
	'''
	ydl_params = {
		'cachedir': None,
		'logger': app.logger.getChild('youtube-dl'),
		'format' : 'bestaudio/best'
	}
	ydl = SimpleYDL(ydl_params)
	res = ydl.extract_info(url, download=False)
	try:
		os.chdir('youtubemp3')
	except Exception as e:
		print "error: %s" % e
		print sys.exc_info()[0]
		
	fileExists = [file for file in os.listdir('.') if res['id'] in file]

	if not len(fileExists)>0:
		res = ydl.extract_info(url, download=True)
		fileExists = [file for file in os.listdir('.') if res['id'] in file]
	
	fileExists = os.path.abspath(fileExists[0])

	return fileExists


  
@app.route('/')
def searcher():
	"""Return a friendly HTTP greeting."""
	return """
<html>
	<body>
	   <script src="//ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
	   <script type="text/javascript">
var keywordSearch = "tcd1304ap";
var gresults = {};


function sendUrlToServer(url){
	// Add necessary hidden inputs to form
	$('input[name="url"]').val(url);

	// If the iFrame has been added before, be sure to delete it
	$("#download_iFrame").remove();

	// Add a new (blank) iFrame to the HTML DOM (right at the end of the body)
	$("body").append('<iframe name="downloadFrame" id="download_iFrame" style="display: none;" src="" />');

	// Before submitting the form, check to see whether this is an iOS/Android device, and change the method of download if it is.
	var iOS = ( navigator.userAgent.match(/(iPad|iPhone|iPod)/g) ? true : false );
	var android = navigator.userAgent.toLowerCase().match(/android/g) ? true : false;
	if (iOS || android)
		$("#form_jsSubmit").attr("target", "_blank");
	
	// Submit the form using JavaScript
	$("#form_jsSubmit").submit();	
}

function searchYoutube() {
	keywordSearch = $("#searchText").val();
	$.get(
		"https://gdata.youtube.com/feeds/api/videos",
		{
			"q":keywordSearch,
			"fields":"entry,entry(media:group(media:thumbnail(@url)))",
			"orderby":"published",
			"start-index":1,
			"max-results":10,
			"v":2,
			"alt":"json"
		},
		function( results ) 
		{
			console.log(results);
			var newHtml="";
			$.each(results["feed"]["entry"], function(i, searchResult)
			{
				newHtml+="<div><img src='" + searchResult["media$group"]["media$thumbnail"][0]["url"] + "' ";
				newHtml+="onClick='javascript:sendUrlToServer(\\"" +
					searchResult["link"][0]["href"] + 
					"\\")'>";
				newHtml+=searchResult["title"]["$t"] + "</br>";
				newHtml+="</div>";
			});
			$("#searchResults").html(newHtml);
		}
	);
}
//$(document).ready(searchYoutube());
		</script>
		<input type="text" id="searchText" name="searchBox">
		<a href="javascript:searchYoutube()">Search</a>
		<div id="searchResults"></div>
		
		<form method="post" target="downloadFrame" action="/ytUrl" id="form_jsSubmit">
			<input type='hidden' name="url"/>
		</form>
	</body>
</html>"""
  
@app.route('/ytUrl', methods=['GET','POST', 'PUT', 'OPTIONS'])
def hello():
	if request.method == 'POST':
		print 'request:\n'
		url = request.form['url']
		url = url[:url.rindex('&')]
		print '****getting: %s *******' % url
		
		audioLocalPath = get_videos(url)

		path, filename = os.path.split(audioLocalPath)

		return send_file(audioLocalPath,
				 mimetype='audio/mpeg',
				 as_attachment=True,
				 attachment_filename=filename)
	return "BAD"

@app.errorhandler(404)
def page_not_found(e):
	"""Return a custom 404 error."""
	return 'Sorry, nothing at this URL.', 404

if __name__ == "__main__":
	app.run(host='0.0.0.0')