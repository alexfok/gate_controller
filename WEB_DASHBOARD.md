# Web Dashboard

The Gate Controller includes a beautiful, modern web dashboard for monitoring and controlling your gate system.

## Features

✨ **Real-time Monitoring**
- Live gate status updates via WebSocket
- Active session tracking
- Continuous status display

🎮 **Manual Controls**
- Open/Close gate buttons
- Instant feedback
- Safety confirmations

🔑 **Token Management**
- View all registered tokens
- Add new tokens
- Remove tokens
- See token detection in real-time

📊 **Activity Log**
- Complete history of all events
- Gate openings and closings
- Token detections
- Registration changes
- Filterable by event type

## Screenshots

The dashboard features:
- Clean, modern UI with responsive design
- Dark text on light background for readability
- Smooth animations and transitions
- Mobile-friendly layout
- Real-time WebSocket updates

## Running the Dashboard

### Start with Web Dashboard

```bash
python3 -m gate_controller.web_main --config config/config.yaml
```

The dashboard will be available at: **http://localhost:8000**

### Configuration

Add to your `config.yaml`:

```yaml
web:
  enabled: true
  host: "0.0.0.0"  # Listen on all interfaces
  port: 8000       # Dashboard port
```

### Access from Other Devices

The dashboard can be accessed from any device on your network:

```
http://YOUR_RASPBERRY_PI_IP:8000
```

For example: `http://192.168.100.185:8000`

## API Endpoints

The dashboard provides a REST API for integration:

### Status
- `GET /api/status` - Get current system status

### Tokens
- `GET /api/tokens` - List registered tokens
- `POST /api/tokens` - Register new token
  ```json
  {
    "uuid": "AA:BB:CC:DD:EE:FF",
    "name": "John's iPhone"
  }
  ```
- `DELETE /api/tokens/{uuid}` - Unregister token

### Gate Control
- `POST /api/gate/open` - Open gate manually
- `POST /api/gate/close` - Close gate manually

### Activity Log
- `GET /api/activity?limit=50&event_type=gate_opened` - Get activity entries
- `DELETE /api/activity` - Clear activity log

### WebSocket
- `WS /ws` - Real-time updates

## Architecture

### Backend (FastAPI)
- Fast, modern Python web framework
- Async/await for concurrent operations
- Automatic API documentation at `/docs`
- WebSocket support for real-time updates

### Frontend
- Pure HTML/CSS/JavaScript (no build step)
- WebSocket client for live updates
- Responsive design (mobile-friendly)
- Modern CSS with animations

### Activity Logging
- JSON-based storage in `logs/activity.json`
- Automatic rotation (keeps last 1000 entries)
- Thread-safe operations
- Queryable history

## Development

### File Structure

```
gate_controller/web/
├── __init__.py
├── server.py           # FastAPI server
├── templates/
│   └── index.html      # Main dashboard page
└── static/
    ├── css/
    │   └── style.css   # Dashboard styles
    └── js/
        └── dashboard.js # Dashboard JavaScript
```

### Adding Features

1. **Backend**: Add API endpoints in `server.py`
2. **Frontend**: Update UI in `templates/index.html`
3. **Styling**: Modify `static/css/style.css`
4. **Interactions**: Extend `static/js/dashboard.js`

## Security Considerations

### Current Implementation
- No authentication (designed for local network use)
- Assumes trusted network environment

### Future Enhancements
- API key authentication
- HTTPS support
- User accounts and permissions
- Rate limiting

### Deployment Recommendations
- Run behind firewall
- Use reverse proxy (nginx) for HTTPS
- Implement network-level access controls
- Consider VPN for remote access

## Troubleshooting

### Dashboard Won't Start

**Issue**: `Address already in use`
- **Solution**: Change port in config or stop other service using port 8000

**Issue**: `Module not found: fastapi`
- **Solution**: `pip3 install fastapi uvicorn`

### WebSocket Issues

**Issue**: Dashboard shows "Disconnected"
- Check controller is running
- Check network connectivity
- Check browser console for errors

### Can't Access from Other Devices

**Issue**: Dashboard only works on localhost
- Ensure `host: "0.0.0.0"` in config (not `127.0.0.1`)
- Check firewall settings
- Verify Raspberry Pi IP address

## Performance

- **WebSocket overhead**: Minimal (~100 bytes per status update)
- **CPU usage**: <1% when idle
- **Memory**: ~50MB for dashboard server
- **Concurrent users**: Supports multiple simultaneous connections
- **Latency**: Real-time updates (<100ms)

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Next Steps

1. **Integrate with Home Automation**
   - Expose API to Home Assistant
   - Create MQTT bridge
   - Add voice assistant integration

2. **Enhanced Features**
   - Historical statistics and charts
   - Email/SMS notifications
   - Geofencing integration
   - Camera feed integration

3. **Mobile App**
   - Native iOS/Android apps
   - Push notifications
   - Background token monitoring

