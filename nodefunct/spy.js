/**
 * User: atatsu
 * Date: 10/9/12
 * Time: 8:34 PM
 */

var util = require('util')
  , assert = require('assert')
  ;

function CallSpy()
{
    var methods = { };

    this.$ = function(methodName)
    {
        methods[methodName] = { args: [ ], returnValue: null, callbackArgs: null, count: 0 };
        this[methodName] = function()
        {
            var args = [ ];
            for (var i = 0; i < arguments.length; i++)
            {
                args.push(arguments[i]);
            }
            methods[methodName].args.push(args);
            methods[methodName].count++;

            for (var i = 0; i < arguments.length; i++)
            {
                if (typeof(arguments[i]) === 'function')
                {
                    arguments[i].apply(undefined, methods[methodName].callbackArgs);
                }
            }

            return methods[methodName].returnValue;
        }

        var spyMethodStats = new (function()
        {
            var args = function()
            {
                return methods[methodName].args;
            }
            this.__defineGetter__('args', args);

            var count = function()
            {
                return methods[methodName].count;
            }
            this.__defineGetter__('count', count);

            this.calledWith = function(searchArg)
            {
                for (var i = 0; i < methods[methodName].args.length; i++)
                {
                    if (methods[methodName].args[i].indexOf(searchArg) !== -1)
                    {
                        return;
                    }
                }
                throw new assert.AssertionError(util.format('`%s` not found in `%s` call args', searchArg, methodName))
            }
        });
        this[util.format('$%s', methodName)] = spyMethodStats;

        var spyMethodOptions = new (function()
        {
            this.returns = function(value)
            {
                methods[methodName].returnValue = value;
                return this;
            }

            this.injectCallbacks = function()
            {
                var args = [ ];
                for (var i = 0; i < arguments.length; i++)
                {
                    args.push(arguments[i]);
                }
                methods[methodName].callbackArgs = args;
                return this;
            }
        });

        return spyMethodOptions;
    }
}

module.exports = function(superCls)
{
    if (superCls !== undefined)
    {
        util.inherits(CallSpy, superCls);
    }

    return new CallSpy();
}
