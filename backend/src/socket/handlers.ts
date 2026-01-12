import { Server, Socket } from 'socket.io'
import { logger } from '../utils/logger.js'

export const setupSocketHandlers = (io: Server) => {
  io.on('connection', (socket: Socket) => {
    logger.info(`Client connected: ${socket.id}`)

    // Handle user joining with their ID
    socket.on('join', (userId: string) => {
      socket.join(`user_${userId}`)
      logger.info(`User ${userId} joined room user_${userId}`)
    })

    // Handle chat messages
    socket.on('chat_message', async (data) => {
      try {
        const { userId, message, conversationId } = data
        
        // TODO: Process message with Noah agent
        logger.info(`Received message from user ${userId}:`, message)
        
        // Simulate Noah's response (to be replaced with actual agent logic)
        const response = {
          messageId: `msg_${Date.now()}`,
          sender: 'noah',
          content: `I received your message: "${message}". I'm still learning how to respond properly!`,
          timestamp: new Date().toISOString(),
          conversationId
        }
        
        // Send response back to user
        socket.to(`user_${userId}`).emit('noah_response', response)
        socket.emit('noah_response', response)
        
      } catch (error) {
        logger.error('Error processing chat message:', error)
        socket.emit('error', { message: 'Failed to process message' })
      }
    })

    // Handle feedback
    socket.on('feedback', async (data) => {
      try {
        const { userId, messageId, feedback } = data
        
        // TODO: Process feedback for learning
        logger.info(`Received feedback from user ${userId}:`, { messageId, feedback })
        
        socket.emit('feedback_received', { messageId, status: 'received' })
        
      } catch (error) {
        logger.error('Error processing feedback:', error)
        socket.emit('error', { message: 'Failed to process feedback' })
      }
    })

    socket.on('disconnect', () => {
      logger.info(`Client disconnected: ${socket.id}`)
    })
  })
}