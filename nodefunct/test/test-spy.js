/**
 * User: atatsu
 * Date: 10/9/12
 * Time: 11:04 PM
 */

var spy = require('../spy')
  , events = require('events')
  , assert = require('assert')
  ;

module.exports['test the spy'] = {

    'test return value': function(test)
    {
        var mockedLib = spy();
        mockedLib.$('fakeMethodName').returns('hi');
        var val = mockedLib.fakeMethodName();
        test.equal(val, 'hi');
        test.done();
    },

    'test called args': function(test)
    {
        var mockedLib = spy();
        mockedLib.$('fakeMethodName');
        mockedLib.fakeMethodName('some', 'args');
        var args = mockedLib.$fakeMethodName.args;
        test.equal(args.length, 1);
        test.equal(args[0].length, 2);
        test.equal(args[0][0], 'some');
        test.equal(args[0][1], 'args');
        test.done();
    },

    'test called args with invalid method': function(test)
    {
        var mockedLib = spy();
        var args = mockedLib.$notSetupMethod;
        test.strictEqual(args, undefined);
        test.done();
    },

    'test number of calls': function(test)
    {
        var mockedLib = spy();
        mockedLib.$('testme');
        mockedLib.testme();
        mockedLib.testme('two');
        mockedLib.testme(3);
        test.equal(mockedLib.$testme.count, 3);
        test.done();
    },

    'test callback args called': function(test)
    {
        var mockedLib = spy();
        mockedLib.$('gimmeSomeCallbacks');
        mockedLib.gimmeSomeCallbacks(function()
        {
            test.done();
        });
    },

    'test injected callback args': function(test)
    {
        var mockedLib = spy();
        mockedLib.$('injectMe').injectCallbacks('herro');
        mockedLib.injectMe(function(injected)
        {
            test.equal(injected, 'herro');
            test.done();
        });
    }
}

module.exports['equality tests'] = {
    'test calledWith': function(test)
    {
        var mockedLib = spy();
        mockedLib.$('callme');
        mockedLib.callme('yes');
        test.doesNotThrow(function() { mockedLib.$callme.calledWith('yes'); }, assert.AssertionError);
        test.throws(function() { mockedLib.$callme.calledWith('no'); }, assert.AssertionError);
        test.done();
    }
}

module.exports['test inheriting'] = {
    'test emit': function(test)
    {
        var mockedLib = spy(events.EventEmitter);
        mockedLib.on('dontblowup', function()
        {
            test.done();
        });
        mockedLib.emit('dontblowup');
    }
}