import express from 'express'
import { createServer } from 'http'
import { Server } from 'socket.io'
import cors from 'cors'
import helmet from 'helmet'
import dotenv from 'dotenv'
import { logger } from './utils/logger.js'
import { errorHandler } from './middleware/errorHandler.js'
import { conversationRoutes } from './routes/conversation.js'
import { profileRoutes } from './routes/profile.js'
import { contentRoutes } from './routes/content.js'
import { setupSocketHandlers } from './socket/handlers.js'

// Load environment variables
dotenv.config()

const app = express()
const server = createServer(app)
const io = new Server(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    methods: ['GET', 'POST'],
  },
})

// Middleware
app.use(helmet())
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}))
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))

// Routes
app.use('/api/conversation', conversationRoutes)
app.use('/api/profile', profileRoutes)
app.use('/api/content', contentRoutes)

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// Socket.IO setup
setupSocketHandlers(io)

// Error handling
app.use(errorHandler)

const PORT = process.env.PORT || 8000

server.listen(PORT, () => {
  logger.info(`Noah backend server running on port ${PORT}`)
})