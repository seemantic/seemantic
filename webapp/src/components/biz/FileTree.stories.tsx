import type { Meta, StoryObj } from '@storybook/react'
import { FileTree } from './FileTree'

const meta = {
  title: 'React/General/FileTree Example',
  component: FileTree,
  tags: ['autodocs'],
} satisfies Meta<typeof FileTree>

export default meta
type Story = StoryObj<typeof meta>

export const Simple: Story = {
  args: {},
}
