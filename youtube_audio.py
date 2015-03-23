import sys
import os
import json
from flask import Flask, request, make_response, jsonify, send_file

import youtube_dl

app = Flask(__name__)
app.config['DEBUG'] = True

# load the Flask server settings from a JSON file
with open('preferences.settings', 'r') as f:
	settings = json.loads(f.read())
	root_url = settings['root_url']
	root_port = settings['port']
	root_ip = settings['ip']
	download_dir = settings['download_dir']


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
	if not os.path.isdir(download_dir):
		os.makedirs(download_dir)
	# change the working-directory to the download_dir
	os.chdir(download_dir)

	def id_exists_in_files(file_name):
		return [file for file in os.listdir('.') if unicode(file_name) in unicode(file, errors='ignore')]

	files_present = id_exists_in_files(res['id'])

	if not files_present:
		# download
		print 'downloading'
		res = ydl.extract_info(url, download=True)
		# scan files for id
		files_present = id_exists_in_files(res['id'])
	else:
		print 'already exists'
	# get the first (assuming only) file in the list
	file_name = os.path.abspath(files_present[0])

	return file_name


@app.route(root_url)
def searcher_API_v2():
	"""Return a friendly HTTP greeting."""
	return """
<html>
	<body>
	   <script src="//ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>
	   <script type="text/javascript">
var keywordSearch = "tcd1304ap";
var gresults = {};
var startIndex = 1;
var numResults = 10;


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

function nextResults(){
	startIndex+=numResults;
	searchYoutube();
}

function prevResults(){
	if (startIndex>1) {
		startIndex-=numResults;
		searchYoutube();
	}
}

function searchYoutube() {
	keywordSearch = $("#searchText").val();
	console.log(keywordSearch);
    var f= encodeURIComponent(keywordSearch);
    console.log(f);
	$.get(
		"https://gdata.youtube.com/feeds/api/videos",
		{
			"q":keywordSearch,
			"fields":"entry,entry(media:group(media:thumbnail(@url)))",
			"orderby":"published",
			"start-index":startIndex,
			"max-results":numResults,
			"v":2,
			"alt":"json"
		},
		function( results ) 
		{
			console.log(results);
			var newHtml="";
			//clear existing results, if there are any
			$("#searchResults").html(newHtml);
			$.each(results["feed"]["entry"], function(i, searchResult)
			{
				newHtml+="<div><img src='" + searchResult["media$group"]["media$thumbnail"][0]["url"] + "' ";
				newHtml+="onClick='javascript:sendUrlToServer(\\"" +
					searchResult["link"][0]["href"] + 
					"\\")'>";
				newHtml+=searchResult["title"]["$t"] + "</br>";
				newHtml+="</div>";
			});
			newHtml+= "</br></br><span><a href='javascript:prevResults()'>Prev Results</a>    "
			newHtml+= "<a href='javascript:nextResults()'>Next Results</a></span>"
			$("#searchResults").html(newHtml);
		}
	);
}
$(document).ready(function(){
	//bind the search function to enter keypress in the textbox
	$('#searchText').keypress(function (event) {
	    if (event.which == 13) {
	        searchYoutube()
	    }
	});
});
		</script>
		<input type="text" id="searchText" style="width: 100%; height:5em;" >
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
	app.run(host=root_ip, port=root_port)
