# Embedding LivePhotos on a web page

I returned from a recent vacaction with lots of LivePhotos, 3-second moving images taken by an iPhone. I wanted to display them along with standard photos on my personal photo album site. It needs to "just work" for my non-techie family members; they use an assortment of devices, including Windows laptops, iPads, Android phones, and iPhones.

I did a bit of Googling, and found an assortment of JavaScript helper libraries. At the top of the list was Apple's press release about their LivePhotosKit. While this looked good at first glance, it was surprisingly unusable and, it turns out, unnecessary. Don't be distracted by the shiny Apple presentation; attempting to use the sample code throws deprecation warnings in the console, but there doesn't seem to be a newer version. Although it's available for download via NPM, the package includes only the minified source — not the original code or a source map. Debugging minimized code without a source map is annoying, and there's no working demo to inspect. After trying to get it to work locally without any luck, I gave up and looked for something easier to use and understand.

A LivePhoto is a video file, and all modern browsers can all play video files natively using the `video` tag. There are three key elements to getting LivePhotos to play nicely along with other photos, with no messy JavaScript dependencies required: re-encode the `.mov` created bythe iPhone to a more portable format, use the `<video>` tag to embed the  content, and serve the page from a real web server.

**Encoding**

A LivePhoto comes from the iPhone as a `.mov` file. Trying to find out which platforms can play which formats led into a rabbit hole of conflicting information about codecs and open vs propriety encoding browser support wars. While Apple devices can play `.mov` files, it was difficult to get a clear answer on whether they would work seamlessly on Windows computers. I decided that `.mp4` was the best format to use to have it just play everywhere.

For a long time, the Safari browser (the default on iPads and iPhones) required a user gesture to play media in a `<video>` tag. As much as I hate auto-playing videos in general, requiring user interaction on each LivePhoto in my vacation album to get it to move for 3 seconds would be a nuisance. Fortunately, as of iOS 10, `<video>` elements will be allowed to autoplay without a user gesture if their source media contains no audio tracks. In a sea of conflicting information, [New `<video>` Policies for iOS](<https://webkit.org/blog/6784/new-video-policies-for-ios/>) had the clearest description I could find about requirements to auto-play video. 

Although they're called LivePhotos, and I wanted to use them as enhanced photos, the `.mov` files do include sound. While re-encoding to `.mp4`, I dropped the audio track. Finally, I also reduced the display size of the video to match my resized-for-web photos.

Searching for how to convert from `.mov` to `.mp4` yields lots of spammy-looking "free online tools",  To re-encode to `.mp4`, drop the audio track, and reduce the resolution (and file size). It's simple to do with the cross-platform, open source [ffmpeg](<https://ffmpeg.org/>):

`ffmpeg -i IMG_1561.mov -an -s 768x576 IMG_1561.mp4`

- `-i` is the input file
- `-an` drops the audio track
- `-s` is the target image size

For one of my LivePhotos, it reduced the filesize from 3.3M to 1.7M — the result was just over half the original size.

To convert all LivePhotos at once:

```
ls *.mov | awk -F '.' '{ print $1 }' | xargs -I {} ffmpeg -i {}.mov -an -s 768x576 {}.mp4
```

**Video tag**

Use the `<video>` tag to embed the file on a page:

```
<video loop muted playsinline autoplay>
  <source src="img/IMG_1561.mp4">
</video>
```

Since there's no audio track, the photo can autoplay. Since I displayed my LivePhotos as part of a slideshow with standard photos, I used `$(slide).find('video')[0].play();` to start the LivePhoto when it came into view.

**Web server**

When working on my site locally, I used `python -m SimpleHTTPServer` to run a local web server for testing. This worked fine when viewing the LivePhotos on Chrome and Firefox, but they didn't play at all on Safari. The reason is that `SimpleHTTPServer` doesn't support range request.

Safari makes a request like this:

Safari makes a range request like this:

```
GET /test.mp4 HTTP/1.1
Range: bytes=0-1
X-Playback-Session-Id: 49E378AD-AB84-4A7F-BE62-C237B36EBDAF
```

`SimpleHTTPServer` responds with

```
Status: 200 OK
Content-Length: 1784332
Content-Type: video/mp4
Server: SimpleHTTP/0.6 Python/2.7.10
```

Apple says ["HTTP servers hosting media files for iOS must support byte-range requests"](
https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/CreatingVideoforSafarioniPhone/CreatingVideoforSafarioniPhone.html#//apple_ref/doc/uid/TP40006514-SW6). Even though it gets all of the content, Safari won't play the file. Most real web servers do support range requests, including the server behind AWS S3 static sites, nginx, and the Apache server on my ancient web hosting account.

**Conclusion**

Displaying LivePhotos on web pages doesn't require using half-baked JavaScript libraries. Instead, prepare the media files for use on the web by re-encoding, resizing, and dropping the audio track, use the HTML5 `video` tag to embed the content, and serve the page from a HTTP/1.1-compliant webserver.

  

---

https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/Using_HTML5_Audio_Video/Introduction/Introduction.html

<https://webkit.org/blog/6784/new-video-policies-for-ios/

Starting in iOS 10, WebKit relaxes its inline and autoplay policies
`<video>` elements will be allowed to autoplay without a user gesture if their source media contains no audio tracks.
`<video>` elements will be allowed to play() without a user gesture if their source media contains no audio tracks, or if their muted property is set to 

but it doesn't have to be this complicated; browser can do it

step 1: re-encode with [ffmpeg](<https://ffmpeg.org/>)

- use mp4 since it plays everywhere
- drop the audio track
- resize

​	ffmpeg -i IMG_1561.mov -an -s 768x576 -c:a copy  IMG_1561.mp4

step 2: use the video tag

	<video loop muted playsinline>
	  <source src="img/013_IMG_1484.mp4">
	</video>
step 3: test on a real webserver

- must support range requests

  `GET /trips/img/013_IMG_1484.mp4 HTTP/1.1`
  `Range: bytes=0-1`

- `python -m SimpleHTTPServer` doesn't; Apache and AWS S3 bucket hosting do