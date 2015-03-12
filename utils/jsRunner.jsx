#targetengine test
$.sblimeRunner = {};
$.sblimeRunner.write = $.write;
$.sblimeRunner.writeln = $.writeln;
$.sblimeRunner.runFile = File(arguments[0]);
$.sblimeRunner.port=arguments[1];
$.write = function(){
	var sock=new Socket();
	sock.open('127.0.0.1:'+$.sblimeRunner.port);
	var args = Array.prototype.slice.call(arguments, 0);
  	sock.write(args.join());
  	sock.close();
};
$.writeln = function(){
	var sock=new Socket();
	sock.open('127.0.0.1:'+$.sblimeRunner.port);
	var args = Array.prototype.slice.call(arguments, 0);
  	sock.write(args.join()+'\r');
  	sock.close();
};
try{
	//$.write($.sblimeRunner.runFile);
	var res=$.evalFile($.sblimeRunner.runFile);
	if (res!==undefined){
		$.writeln('Indesign returned: '+res.toString());
	}
	$.writeln('[Finished]');
}catch(e){
	$.writeln('[----------------]');
    $.writeln('  Error:'+e);
	$.writeln('    File:'+File(e.fileName).fsName||'[current]');
	$.writeln('    Line:'+e.line||'[unkown]');
	$.writeln('[Exited with error]');
}finally{
	$.write('<ServerClose/>');
	$.write=$.sblimeRunner.write;
	$.writeln=$.sblimeRunner.writeln;
	delete $.sblimeRunner;
}