const database = require('../config/database');

class Controller {
  constructor(data) {
    this.id = data.id;
    this.serialNumber = data.serial_number;
    this.type = data.type;
    this.name = data.name;
    this.userId = data.user_id;
    this.latitude = data.latitude;
    this.longitude = data.longitude;
    this.status = data.status;
    this.lastSeen = data.last_seen;
    this.createdAt = data.created_at;
    this.updatedAt = data.updated_at;
    this.config = data.config ? JSON.parse(data.config) : {};
  }

  static async create(controllerData) {
    const { serialNumber, type, latitude = null, longitude = null } = controllerData;
    
    const result = await database.query(
      'INSERT INTO controllers (serial_number, type, latitude, longitude) VALUES (?, ?, ?, ?)',
      [serialNumber, type, latitude, longitude]
    );
    
    return await Controller.findById(result.insertId);
  }

  static async findById(id) {
    const rows = await database.query('SELECT * FROM controllers WHERE id = ?', [id]);
    return rows.length > 0 ? new Controller(rows[0]) : null;
  }

  static async findBySerialNumber(serialNumber) {
    const rows = await database.query('SELECT * FROM controllers WHERE serial_number = ?', [serialNumber]);
    return rows.length > 0 ? new Controller(rows[0]) : null;
  }

  static async findAll(limit = 50, offset = 0) {
    const rows = await database.query(
      'SELECT * FROM controllers ORDER BY created_at DESC LIMIT ? OFFSET ?',
      [limit, offset]
    );
    return rows.map(row => new Controller(row));
  }

  static async findByUser(userId) {
    const rows = await database.query(
      'SELECT * FROM controllers WHERE user_id = ? ORDER BY name, serial_number',
      [userId]
    );
    return rows.map(row => new Controller(row));
  }

  static async findUnbound() {
    const rows = await database.query(
      'SELECT * FROM controllers WHERE user_id IS NULL ORDER BY last_seen DESC, created_at DESC'
    );
    return rows.map(row => new Controller(row));
  }

  static async findOnline() {
    const rows = await database.query(
      "SELECT * FROM controllers WHERE status = 'online' ORDER BY last_seen DESC"
    );
    return rows.map(row => new Controller(row));
  }

  async update(data) {
    const { name, latitude, longitude, config } = data;
    await database.query(
      'UPDATE controllers SET name = ?, latitude = ?, longitude = ?, config = ?, updated_at = NOW() WHERE id = ?',
      [name, latitude, longitude, JSON.stringify(config || {}), this.id]
    );
    
    // Refresh data
    const updated = await Controller.findById(this.id);
    Object.assign(this, updated);
  }

  async bindToUser(userId) {
    await database.query(
      'UPDATE controllers SET user_id = ?, updated_at = NOW() WHERE id = ?',
      [userId, this.id]
    );
    this.userId = userId;
  }

  async unbind() {
    await database.query(
      'UPDATE controllers SET user_id = NULL, updated_at = NOW() WHERE id = ?',
      [this.id]
    );
    this.userId = null;
  }

  async updateStatus(status, timestamp = null) {
    const lastSeen = timestamp ? new Date(timestamp) : new Date();
    await database.query(
      'UPDATE controllers SET status = ?, last_seen = ?, updated_at = NOW() WHERE id = ?',
      [status, lastSeen, this.id]
    );
    this.status = status;
    this.lastSeen = lastSeen;
  }

  async addData(data, timestamp = null) {
    const dataTimestamp = timestamp ? new Date(timestamp) : new Date();
    await database.query(
      'INSERT INTO controller_data (controller_id, data, timestamp) VALUES (?, ?, ?)',
      [this.id, JSON.stringify(data), dataTimestamp]
    );

    // Update last seen
    await this.updateStatus('online', dataTimestamp);
  }

  async getData(limit = 100, offset = 0, startDate = null, endDate = null) {
    let query = 'SELECT * FROM controller_data WHERE controller_id = ?';
    let params = [this.id];

    if (startDate) {
      query += ' AND timestamp >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND timestamp <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?';
    params.push(limit, offset);

    const rows = await database.query(query, params);
    return rows.map(row => ({
      ...row,
      data: JSON.parse(row.data)
    }));
  }

  async getLatestData() {
    const rows = await database.query(
      'SELECT * FROM controller_data WHERE controller_id = ? ORDER BY timestamp DESC LIMIT 1',
      [this.id]
    );
    
    if (rows.length === 0) return null;
    
    return {
      ...rows[0],
      data: JSON.parse(rows[0].data)
    };
  }

  async delete() {
    await database.transaction(async (connection) => {
      // Delete all data first
      await connection.execute('DELETE FROM controller_data WHERE controller_id = ?', [this.id]);
      // Delete controller
      await connection.execute('DELETE FROM controllers WHERE id = ?', [this.id]);
    });
  }

  static async getStats() {
    const [totalCount] = await database.query('SELECT COUNT(*) as count FROM controllers');
    const [onlineCount] = await database.query("SELECT COUNT(*) as count FROM controllers WHERE status = 'online'");
    const [boundCount] = await database.query('SELECT COUNT(*) as count FROM controllers WHERE user_id IS NOT NULL');
    
    return {
      total: totalCount.count,
      online: onlineCount.count,
      offline: totalCount.count - onlineCount.count,
      bound: boundCount.count,
      unbound: totalCount.count - boundCount.count
    };
  }

  isOnline() {
    if (this.status !== 'online' || !this.lastSeen) return false;
    
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return new Date(this.lastSeen) > fiveMinutesAgo;
  }

  toJSON() {
    return {
      id: this.id,
      serialNumber: this.serialNumber,
      type: this.type,
      name: this.name,
      userId: this.userId,
      latitude: this.latitude,
      longitude: this.longitude,
      status: this.status,
      lastSeen: this.lastSeen,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      config: this.config,
      isOnline: this.isOnline()
    };
  }
}

module.exports = Controller;