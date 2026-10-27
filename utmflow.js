/**
 * UtmFlow Tracking Pixel & Checkout Link Decorator Engine (v2.0)
 * Native Zero-Dependency Tracking Script
 * 
 * Features:
 * - Persistent UTM & SRC Capture (Cookie + localStorage)
 * - Meta CAPI Compliant _fbp & _fbc Generation & Management
 * - Automatic Checkout Link Decorator (Kiwify, Hotmart, Greenn, Cakto, Wiapy, Eduzz, etc.)
 * - Automatic PageView Beacon & InitiateCheckout Auto-Detection
 */

(function (window, document) {
    'use strict';

    var COOKIE_PREFIX = 'uf_';
    var COOKIE_EXPIRY_DAYS = 90;
    var TRACKING_ENDPOINT = '/api/track';

    // Helper: Set Cookie with SameSite and Max-Age
    function setCookie(name, value, days) {
        var expires = '';
        if (days) {
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }
        document.cookie = name + '=' + encodeURIComponent(value || '') + expires + '; path=/; SameSite=Lax';
    }

    // Helper: Get Cookie
    function getCookie(name) {
        var nameEQ = name + '=';
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) {
                return decodeURIComponent(c.substring(nameEQ.length, c.length));
            }
        }
        return null;
    }

    // Helper: Parse URL parameters
    function getUrlParams() {
        var params = {};
        var search = window.location.search.substring(1);
        if (!search) return params;
        var pairs = search.split('&');
        for (var i = 0; i < pairs.length; i++) {
            var pair = pairs[i].split('=');
            if (pair[0]) {
                params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
            }
        }
        return params;
    }

    // 1. Meta _fbp Generation & Persistence (fb.1.timestamp.random)
    function ensureFbp() {
        var existingFbp = getCookie('_fbp') || localStorage.getItem('uf_fbp');
        if (existingFbp && existingFbp.indexOf('fb.1.') === 0) {
            setCookie('_fbp', existingFbp, COOKIE_EXPIRY_DAYS);
            return existingFbp;
        }
        var timestamp = Date.now();
        var randomNumber = Math.floor(Math.random() * 8999999999 + 1000000000);
        var newFbp = 'fb.1.' + timestamp + '.' + randomNumber;
        setCookie('_fbp', newFbp, COOKIE_EXPIRY_DAYS);
        try { localStorage.setItem('uf_fbp', newFbp); } catch (e) {}
        return newFbp;
    }

    // 2. Meta _fbc Generation (fb.1.timestamp.fbclid)
    function ensureFbc(urlParams) {
        var fbclid = urlParams.fbclid;
        if (fbclid) {
            var timestamp = Date.now();
            var newFbc = 'fb.1.' + timestamp + '.' + fbclid;
            setCookie('_fbc', newFbc, COOKIE_EXPIRY_DAYS);
            try { localStorage.setItem('uf_fbc', newFbc); } catch (e) {}
            return newFbc;
        }
        return getCookie('_fbc') || localStorage.getItem('uf_fbc') || '';
    }

    // 3. Capture UTM parameters and persist
    var urlParams = getUrlParams();
    var trackedParams = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'src', 'sck'];
    var currentTrackingData = {};

    // Restore from localStorage first
    try {
        var stored = localStorage.getItem('utmflow_utms');
        if (stored) {
            currentTrackingData = JSON.parse(stored) || {};
        }
    } catch (e) {}

    // Overwrite with URL params if present
    for (var i = 0; i < trackedParams.length; i++) {
        var p = trackedParams[i];
        if (urlParams[p]) {
            currentTrackingData[p] = urlParams[p];
            setCookie(COOKIE_PREFIX + p, urlParams[p], COOKIE_EXPIRY_DAYS);
        } else if (!currentTrackingData[p]) {
            var cookieVal = getCookie(COOKIE_PREFIX + p);
            if (cookieVal) currentTrackingData[p] = cookieVal;
        }
    }

    // Default source if completely empty
    if (!currentTrackingData['utm_source']) {
        var referrer = document.referrer || '';
        if (referrer.indexOf('facebook.com') > -1 || referrer.indexOf('fb.me') > -1) {
            currentTrackingData['utm_source'] = 'facebook';
        } else if (referrer.indexOf('instagram.com') > -1) {
            currentTrackingData['utm_source'] = 'instagram';
        } else if (referrer.indexOf('google.') > -1) {
            currentTrackingData['utm_source'] = 'google';
        } else if (referrer.indexOf('tiktok.com') > -1) {
            currentTrackingData['utm_source'] = 'tiktok';
        } else if (referrer.indexOf('youtube.com') > -1) {
            currentTrackingData['utm_source'] = 'youtube';
        } else {
            currentTrackingData['utm_source'] = 'direto';
        }
    }

    // Persist _fbp and _fbc
    currentTrackingData['fbp'] = ensureFbp();
    currentTrackingData['fbc'] = ensureFbc(urlParams);

    try {
        localStorage.setItem('utmflow_utms', JSON.stringify(currentTrackingData));
    } catch (e) {}

    // 4. Send Event Beacon to UtmFlow Server
    function sendTrackingEvent(eventName, extraData) {
        var payload = {
            event_name: eventName,
            event_id: 'ev_' + Date.now() + '_' + Math.floor(Math.random() * 1000000),
            url: window.location.href,
            referrer: document.referrer,
            utm_source: currentTrackingData.utm_source || '',
            utm_medium: currentTrackingData.utm_medium || '',
            utm_campaign: currentTrackingData.utm_campaign || '',
            utm_content: currentTrackingData.utm_content || '',
            utm_term: currentTrackingData.utm_term || '',
            src: currentTrackingData.src || '',
            sck: currentTrackingData.sck || '',
            fbc: currentTrackingData.fbc || '',
            fbp: currentTrackingData.fbp || ''
        };

        if (extraData && typeof extraData === 'object') {
            for (var key in extraData) {
                if (extraData.hasOwnProperty(key)) {
                    payload[key] = extraData[key];
                }
            }
        }

        var jsonStr = JSON.stringify(payload);
        if (navigator.sendBeacon) {
            navigator.sendBeacon(TRACKING_ENDPOINT, jsonStr);
        } else {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', TRACKING_ENDPOINT, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(jsonStr);
        }
    }

    // Auto-fire PageView
    sendTrackingEvent('PageView');

    // 5. Automatic Checkout Link Decorator
    var checkoutDomains = [
        'kiwify.com.br', 'hotmart.com', 'greenn.com.br', 'cakto.com.br',
        'wiapy.com', 'eduzz.com', 'monetizze.com.br', 'braip.com',
        'perfectpay.com.br', 'kirvano.com', 'pepper.com.br', 'pay.kiwify.com.br'
    ];

    function decorateUrl(originalUrl) {
        if (!originalUrl || originalUrl.indexOf('javascript:') === 0 || originalUrl.indexOf('#') === 0) {
            return originalUrl;
        }

        try {
            var urlObj = new URL(originalUrl, window.location.origin);
            var isCheckout = false;

            for (var i = 0; i < checkoutDomains.length; i++) {
                if (urlObj.hostname.indexOf(checkoutDomains[i]) > -1) {
                    isCheckout = true;
                    break;
                }
            }

            // Also check for checkout-like paths
            var path = urlObj.pathname.toLowerCase();
            if (path.indexOf('/pay') > -1 || path.indexOf('/checkout') > -1 || path.indexOf('/comprar') > -1) {
                isCheckout = true;
            }

            if (isCheckout) {
                for (var key in currentTrackingData) {
                    if (currentTrackingData.hasOwnProperty(key) && currentTrackingData[key]) {
                        if (!urlObj.searchParams.has(key)) {
                            urlObj.searchParams.set(key, currentTrackingData[key]);
                        }
                    }
                }
                // Ensure sck and src are passed for Hotmart/Kiwify
                if (!urlObj.searchParams.has('src') && currentTrackingData.utm_source) {
                    urlObj.searchParams.set('src', currentTrackingData.utm_source);
                }
                if (!urlObj.searchParams.has('sck') && currentTrackingData.utm_campaign) {
                    urlObj.searchParams.set('sck', currentTrackingData.utm_campaign);
                }
                return urlObj.toString();
            }
        } catch (e) {
            return originalUrl;
        }
        return originalUrl;
    }

    function decorateAllLinks() {
        var links = document.querySelectorAll('a[href]');
        for (var i = 0; i < links.length; i++) {
            var link = links[i];
            var href = link.getAttribute('href');
            if (href && !link.getAttribute('data-uf-decorated')) {
                var decorated = decorateUrl(href);
                if (decorated !== href) {
                    link.setAttribute('href', decorated);
                    link.setAttribute('data-uf-decorated', 'true');
                    
                    // Hook click for InitiateCheckout event
                    link.addEventListener('click', function () {
                        sendTrackingEvent('InitiateCheckout', { destination: decorated });
                    });
                }
            }
        }

        // Decorate checkout forms
        var forms = document.querySelectorAll('form[action]');
        for (var j = 0; j < forms.length; j++) {
            var form = forms[j];
            var action = form.getAttribute('action');
            if (action && !form.getAttribute('data-uf-decorated')) {
                var decoratedForm = decorateUrl(action);
                if (decoratedForm !== action) {
                    form.setAttribute('action', decoratedForm);
                    form.setAttribute('data-uf-decorated', 'true');
                }
            }
        }
    }

    // Run immediately and on DOM readiness
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', decorateAllLinks);
    } else {
        decorateAllLinks();
    }

    // Run again periodically for dynamically added checkout buttons/elements
    setInterval(decorateAllLinks, 2000);

    // Global Public API
    window.UtmFlow = {
        track: function (eventName, data) {
            sendTrackingEvent(eventName, data);
        },
        getData: function () {
            return Object.assign({}, currentTrackingData);
        },
        decorate: decorateUrl
    };

    // Alias for backwards compatibility
    window.NexusTrack = window.UtmFlow;

})(window, document);
