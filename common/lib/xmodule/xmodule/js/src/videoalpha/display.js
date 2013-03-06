// Generated by CoffeeScript 1.4.0
(function() {

  this.VideoAlpha = (function() {

    function VideoAlpha(element) {
      var sub,
        _this = this;
      this.el = $(element).find('.video');
      this.id = this.el.attr('id').replace(/video_/, '');
      this.start = this.el.data('start');
      this.end = this.el.data('end');
      this.caption_data_dir = this.el.data('caption-data-dir');
      this.caption_asset_path = this.el.data('caption-asset-path');
      this.show_captions = this.el.data('show-captions').toString() === "true";
      this.el = $("#video_" + this.id);
      if (this.parseYoutubeId(this.el.data("streams")) === true) {
        this.videoType = "youtube";
        this.fetchMetadata();
        this.parseSpeed();
      } else {
        this.videoType = "html5";
        this.parseHtml5Sources(this.el.data('mp4-source'), this.el.data('webm-source'), this.el.data('ogg-source'));
        this.speeds = ['0.75', '1.0', '1.25', '1.50'];
        sub = this.el.data('sub');
        if ((typeof sub !== "string") || (sub.length === 0)) {
          sub = "";
          this.show_captions = false;
        }
        this.videos = {
          "0.75": sub,
          "1.0": sub,
          "1.25": sub,
          "1.5": sub
        };
        this.setSpeed($.cookie('video_speed'));
      }
      $("#video_" + this.id).data('video', this).addClass('video-load-complete');
      if (this.show_captions === true) {
        this.hide_captions = $.cookie('hide_captions') === 'true';
      } else {
        this.hide_captions = true;
        $.cookie('hide_captions', this.hide_captions, {
          expires: 3650,
          path: '/'
        });
        this.el.addClass('closed');
      }
      if (((this.videoType === "youtube") && YT.Player) || ((this.videoType === "html5") && HTML5Video.Player)) {
        this.embed();
      } else {
        if (this.videoType === "youtube") {
          window.onYouTubePlayerAPIReady = function() {
            return _this.embed();
          };
        } else if (this.videoType === "html5") {
          window.onHTML5PlayerAPIReady = function() {
            return _this.embed();
          };
        }
      }
    }

    VideoAlpha.prototype.youtubeId = function(speed) {
      return this.videos[speed || this.speed];
    };

    VideoAlpha.prototype.parseYoutubeId = function(videos) {
      var _this = this;
      if ((typeof videos !== "string") || (videos.length === 0)) {
        return false;
      }
      this.videos = {};
      $.each(videos.split(/,/), function(index, video) {
        var speed;
        speed = void 0;
        video = video.split(/:/);
        speed = parseFloat(video[0]).toFixed(2).replace(/\.00$/, ".0");
        return _this.videos[speed] = video[1];
      });
      return true;
    };

    VideoAlpha.prototype.parseHtml5Sources = function(mp4Source, webmSource, oggSource) {
      this.html5Sources = {
        mp4: null,
        webm: null,
        ogg: null
      };
      if ((typeof mp4Source === "string") && (mp4Source.length > 0)) {
        this.html5Sources.mp4 = mp4Source;
      }
      if ((typeof webmSource === "string") && (webmSource.length > 0)) {
        this.html5Sources.webm = webmSource;
      }
      if ((typeof oggSource === "string") && (oggSource.length > 0)) {
        return this.html5Sources.ogg = oggSource;
      }
    };

    VideoAlpha.prototype.parseSpeed = function() {
      this.speeds = ($.map(this.videos, function(url, speed) {
        return speed;
      })).sort();
      return this.setSpeed($.cookie('video_speed'));
    };

    VideoAlpha.prototype.setSpeed = function(newSpeed, updateCookie) {
      if (this.speeds.indexOf(newSpeed) !== -1) {
        this.speed = newSpeed;
        if (updateCookie !== false) {
          return $.cookie("video_speed", "" + newSpeed, {
            expires: 3650,
            path: "/"
          });
        }
      } else {
        return this.speed = "1.0";
      }
    };

    VideoAlpha.prototype.embed = function() {
      return this.player = new VideoPlayerAlpha({
        video: this
      });
    };

    VideoAlpha.prototype.fetchMetadata = function(url) {
      var _this = this;
      this.metadata = {};
      return $.each(this.videos, function(speed, url) {
        return $.get("https://gdata.youtube.com/feeds/api/videos/" + url + "?v=2&alt=jsonc", (function(data) {
          return _this.metadata[data.data.id] = data.data;
        }), 'jsonp');
      });
    };

    VideoAlpha.prototype.getDuration = function() {
      return this.metadata[this.youtubeId()].duration;
    };

    VideoAlpha.prototype.log = function(eventName) {
      var logInfo;
      logInfo = {
        id: this.id,
        code: this.youtubeId(),
        currentTime: this.player.currentTime,
        speed: this.speed
      };
      if (this.videoType === "youtube") {
        logInfo.code = this.youtubeId();
      } else {
        if (this.videoType === "html5") {
          logInfo.code = "html5";
        }
      }
      return Logger.log(eventName, logInfo);
    };

    return VideoAlpha;

  })();

}).call(this);