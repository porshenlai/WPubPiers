function speak( text, locale="zh-TW", pitch=1, rate=1 ){ // zh-TW, ja-JP, fr-FR, de-DE
	return new Promise(function( or, oe ){
		if( window.speechSynthesis.speaking ) return oe("speechSynthesis.speaking"); 
		var ut,retries = 100,timer;
		ut = new SpeechSynthesisUtterance( text )
		ut.onend = or;
		ut.onerror = oe;
		ut.pitch = pitch;
		ut.rate = rate;
		timer = setInterval(function(){
			retries--;
			voices = window.speechSynthesis.getVoices();
			if( voices ){
				ut.voice = voices.find( function (v) { return v.lang === locale; } );
				window.speechSynthesis.speak( ut );
			}else if( retries > 0 ) return;
			if(timer){ clearInterval(timer); timer=undefined; }
		},100);
	});
}

function listen( grammar = undefined, locale="zh-TW" ){ //"en-US"
	var SpeechRecognition = SpeechRecognition || webkitSpeechRecognition;
	return new Promise( function( or, oe ){
		var results=[], R = new SpeechRecognition();
		if(grammar){
			var SpeechGrammarList = SpeechGrammarList || webkitSpeechGrammarList;
			R.grammars = new SpeechGrammarList();
			R.grammars.addFromString( "#JSGF V1.0; grammar phrase; "+grammar+";", 1 );
		}
		R.lang = locale;
		R.interimResults = false;
		R.maxAlternatives = 3;
		R.onresult = function(event){ results = event.results; };
		R.onspeechend = function(event){ R.stop(); };
		R.onerror = function(event){ oe(event.error); };
		R.onend = function(event){ or(results); };
		//R.onaudiostart = function(event){ console.log('SpeechRecognition.onaudiostart'); };
		//R.onaudioend = function(event){ console.log('SpeechRecognition.onaudioend'); };
		//R.onnomatch = function(event){ console.log('SpeechRecognition.onnomatch'); };
		//R.onsoundstart = function(event){ console.log('SpeechRecognition.onsoundstart'); };
  		//R.onsoundend = function(event){ console.log('SpeechRecognition.onsoundend'); };
		//R.onspeechstart = function(event){ console.log('SpeechRecognition.onspeechstart'); };
		//R.onstart = function(event){ console.log('SpeechRecognition.onstart'); };
		R.start();
	} );
}
