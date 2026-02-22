import type { Meta, StoryObj } from '@storybook/react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../card';
import { Button } from '../button';

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card Description</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content goes here.</p>
      </CardContent>
      <CardFooter>
        <Button>Action</Button>
      </CardFooter>
    </Card>
  ),
};

export const AssetCard: Story = {
  render: () => (
    <Card className="w-[300px] bg-[#111111] border-[#262626]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white">BTC/EUR</CardTitle>
          <span className="text-trade-green text-sm font-medium">+2.5%</span>
        </div>
        <CardDescription>Bitcoin</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">€67,234.50</div>
        <div className="text-sm text-muted-foreground">Volume: 1.2B</div>
      </CardContent>
    </Card>
  ),
};

export const MetricCard: Story = {
  render: () => (
    <Card className="w-[250px] bg-[#111111] border-[#262626]">
      <CardContent className="pt-6">
        <div className="text-sm text-muted-foreground">Portfolio Value</div>
        <div className="text-3xl font-bold text-white mt-2">€125,430</div>
        <div className="text-sm text-trade-green mt-1">+€2,340 (1.9%)</div>
      </CardContent>
    </Card>
  ),
};

export const OrderCard: Story = {
  render: () => (
    <Card className="w-[400px] bg-[#111111] border-[#262626]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base text-white">Active Order</CardTitle>
          <span className="px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-500 text-xs">
            Pending
          </span>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-muted-foreground">Symbol</div>
            <div className="text-sm font-medium text-white">BTC/EUR</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Side</div>
            <div className="text-sm font-medium text-trade-green">Buy</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Amount</div>
            <div className="text-sm font-medium text-white">0.5 BTC</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Price</div>
            <div className="text-sm font-medium text-white">€67,000</div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-0">
        <Button variant="outline" size="sm" className="w-full">
          Cancel Order
        </Button>
      </CardFooter>
    </Card>
  ),
};
