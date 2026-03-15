/**
 * Keystroke Telemetry — Browser Capture Layer
 * 
 * Hooks into any text input and captures typing patterns:
 * - Insert/delete events with millisecond timing
 * - Cognitive pauses (>2s gaps)
 * - Hesitation signals (deletion bursts, rewrites)
 * - Discarded messages (typed then abandoned)
 * 
 * Events are batched and flushed to your endpoint on submit
 * or when the buffer is abandoned (blur + timeout).
 * 
 * Usage:
 *   KeystrokeTelemetry.attach('chat-input', {
 *     agentType: 'assistant',
 *     flushEndpoint: '/api/telemetry/keystrokes'
 *   });
 *   KeystrokeTelemetry.onSubmit('chat-input', finalText);
 * 
 * Schema: keystroke_telemetry/v2
 */

const KeystrokeTelemetry = (function() {
    'use strict';

    const SCHEMA = 'keystroke_telemetry/v2';
    const DEFAULT_ENDPOINT = '/api/telemetry/keystrokes';
    const ABANDON_TIMEOUT_MS = 30000;
    const BATCH_SIZE = 200;

    const inputs = {};

    function _genId(len) {
        const a = 'abcdef0123456789';
        let s = '';
        for (let i = 0; i < len; i++) s += a[Math.floor(Math.random() * a.length)];
        return s;
    }

    function _nowMs() {
        return Date.now();
    }

    function _getVisitorId() {
        let vid = sessionStorage.getItem('kt_visitor_id');
        if (!vid) {
            vid = _genId(12);
            sessionStorage.setItem('kt_visitor_id', vid);
        }
        return vid;
    }

    /**
     * Attach keystroke capture to a text input element.
     * @param {string} inputId - DOM element ID
     * @param {Object} config - { agentType, entityId, pageSource, flushEndpoint }
     */
    function attach(inputId, config = {}) {
        const el = document.getElementById(inputId);
        if (!el) return;

        const state = {
            inputId: inputId,
            sessionId: _genId(12),
            messageId: _genId(10),
            agentType: config.agentType || 'unknown',
            entityId: config.entityId || '',
            pageSource: config.pageSource || window.location.pathname,
            flushEndpoint: config.flushEndpoint || DEFAULT_ENDPOINT,
            events: [],
            seq: 0,
            lastEventMs: 0,
            abandonTimer: null,
            lastCognitiveState: 'neutral',
            lastHesitation: 0,
        };
        inputs[inputId] = state;

        el.addEventListener('keydown', function(e) {
            const now = _nowMs();
            const delta = state.lastEventMs ? (now - state.lastEventMs) : 0;

            let eventType = 'insert';
            let key = e.key;

            if (e.key === 'Backspace') {
                eventType = 'backspace';
                key = 'Backspace';
            } else if (e.key === 'Delete') {
                eventType = 'delete';
                key = 'Delete';
            } else if (e.key === 'Enter') {
                return;
            } else if (e.key.length > 1) {
                return;
            }

            state.seq++;
            state.events.push({
                schema: SCHEMA,
                seq: state.seq,
                message_id: state.messageId,
                timestamp_ms: now,
                delta_ms: delta,
                event_type: eventType,
                key: key,
                cursor_pos: el.selectionStart || 0,
                buffer: el.value + (eventType === 'insert' ? key : ''),
                buffer_len: el.value.length + (eventType === 'insert' ? 1 : 0),
            });
            state.lastEventMs = now;

            if (state.events.length >= BATCH_SIZE) {
                _flush(state, false);
            }
            _resetAbandonTimer(state);
        });

        el.addEventListener('paste', function() {
            const now = _nowMs();
            state.seq++;
            state.events.push({
                schema: SCHEMA,
                seq: state.seq,
                message_id: state.messageId,
                timestamp_ms: now,
                delta_ms: state.lastEventMs ? (now - state.lastEventMs) : 0,
                event_type: 'paste',
                key: '[paste]',
                cursor_pos: el.selectionStart || 0,
                buffer: el.value,
                buffer_len: el.value.length,
            });
            state.lastEventMs = now;
        });

        el.addEventListener('blur', function() {
            if (state.events.length > 0 && el.value.length > 0) {
                _resetAbandonTimer(state);
            }
        });

        el.addEventListener('focus', function() {
            if (state.abandonTimer) {
                clearTimeout(state.abandonTimer);
                state.abandonTimer = null;
            }
        });
    }

    function _resetAbandonTimer(state) {
        if (state.abandonTimer) clearTimeout(state.abandonTimer);
        state.abandonTimer = setTimeout(() => {
            if (state.events.length > 0) {
                state.events.push({
                    schema: SCHEMA,
                    seq: state.seq + 1,
                    message_id: state.messageId,
                    timestamp_ms: _nowMs(),
                    delta_ms: ABANDON_TIMEOUT_MS,
                    event_type: 'discard',
                    key: '',
                    cursor_pos: 0,
                    buffer: '',
                    buffer_len: 0,
                });
                _flush(state, false);
            }
        }, ABANDON_TIMEOUT_MS);
    }

    /**
     * Call when the user submits their message.
     * Returns a promise with the server's cognitive analysis.
     */
    function onSubmit(inputId, finalText) {
        const state = inputs[inputId];
        if (!state) return Promise.resolve(null);

        state.seq++;
        state.events.push({
            schema: SCHEMA,
            seq: state.seq,
            message_id: state.messageId,
            timestamp_ms: _nowMs(),
            delta_ms: state.lastEventMs ? (_nowMs() - state.lastEventMs) : 0,
            event_type: 'submit',
            key: '',
            cursor_pos: finalText.length,
            buffer: finalText,
            buffer_len: finalText.length,
        });

        return _flush(state, true);
    }

    /**
     * Get the last cognitive state for an input.
     */
    function getLastState(inputId) {
        const state = inputs[inputId];
        if (!state) return null;
        return {
            cognitive_state: state.lastCognitiveState || 'neutral',
            hesitation: state.lastHesitation || 0
        };
    }

    function _flush(state, isSubmit) {
        if (state.events.length === 0) return Promise.resolve(null);

        const payload = {
            session_id: state.sessionId,
            message_id: state.messageId,
            visitor_id: _getVisitorId(),
            agent_type: state.agentType,
            entity_id: state.entityId,
            page_source: state.pageSource,
            events: state.events,
            submitted: isSubmit,
        };

        const promise = fetch(state.flushEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }).then(function(r) { return r.json(); })
          .then(function(data) {
            if (data && data.cognitive_state) {
                state.lastCognitiveState = data.cognitive_state;
                state.lastHesitation = data.hesitation_score || 0;
            }
            return data;
        }).catch(function() { return null; });

        // Reset for next message
        state.events = [];
        state.seq = 0;
        state.messageId = _genId(10);
        if (state.abandonTimer) {
            clearTimeout(state.abandonTimer);
            state.abandonTimer = null;
        }

        return promise;
    }

    function setEntityId(inputId, entityId) {
        if (inputs[inputId]) {
            inputs[inputId].entityId = entityId;
        }
    }

    return { attach, onSubmit, setEntityId, getLastState };
})();
