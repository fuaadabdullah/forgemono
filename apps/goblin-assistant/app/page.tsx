"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Cpu, Users, Database, Globe, Star, TrendingUp, MessageSquare, DollarSign } from 'lucide-react';
import { Button } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';

export default function Home() {
  const router = useRouter();
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const handleGetStarted = () => {
    router.push('/chat');
  };

  const handleLearnMore = () => {
    router.push('/chat');
  };

  const features = [
    {
      icon: <Cpu className="w-6 h-6" />,
      title: "Intelligent Routing",
      description: "Automatically selects the best AI model for each task based on complexity, cost, and performance."
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Privacy First",
      description: "Your data stays secure with local processing options and encrypted cloud connections."
    },
    {
      icon: <DollarSign className="w-6 h-6" />,
      title: "Multi-Provider",
      description: "Access multiple AI providers seamlessly with intelligent fallback and load balancing."
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Developer Focused",
      description: "Built for developers with comprehensive APIs, webhooks, and integration tools."
    }
  ];

  const useCases = [
    {
      icon: <MessageSquare className="w-8 h-8" />,
      title: "Code Assistance",
      description: "Get help with debugging, code reviews, and implementation guidance."
    },
    {
      icon: <Database className="w-8 h-8" />,
      title: "Data Analysis",
      description: "Analyze datasets, generate insights, and create visualizations."
    },
    {
      icon: <Globe className="w-8 h-8" />,
      title: "Research & Learning",
      description: "Access knowledge from multiple sources with intelligent summarization."
    }
  ];

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-20 left-10 w-72 h-72 bg-accent-green/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-40 right-10 w-96 h-96 bg-info/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
          <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-warning/10 rounded-full blur-3xl animate-pulse delay-500"></div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10">
        {/* Navigation */}
        <nav className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-r from-accent-green to-info rounded-xl flex items-center justify-center shadow-lg shadow-accent-green/20">
                <Star className="w-6 h-6 text-bg-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-text-primary font-mono">GoblinOS Assistant</h1>
                <p className="text-xs text-text-secondary font-mono">Your intelligent development companion</p>
              </div>
            </div>
            <div className="hidden md:flex items-center space-x-4">
              <Button variant="ghost" className="text-text-secondary hover:text-text-primary font-mono">
                Documentation
              </Button>
              <Button variant="ghost" className="text-text-secondary hover:text-text-primary font-mono">
                API
              </Button>
              <Button 
                onClick={handleGetStarted}
                className="bg-accent-green text-bg-primary hover:bg-accent-green-bright font-semibold px-6 py-2 rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-accent-green/25 glow"
              >
                Get Started
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <main className="container mx-auto px-6 pb-20">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <Badge variant="outline" className="bg-bg-secondary border-border-subtle text-text-primary mb-6 backdrop-blur-sm font-mono">
              <Star className="w-4 h-4 mr-2" />
              AI-Powered Development Assistant
            </Badge>

            {/* Title */}
            <h1 className={`text-5xl md:text-7xl font-bold text-text-primary mb-6 transition-all duration-1000 ${
              isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            } font-mono`}>
              Build Smarter.
              <br />
              <span className="bg-gradient-to-r from-accent-green via-info to-warning bg-clip-text text-transparent">
                Work Faster.
              </span>
            </h1>

            {/* Subtitle */}
            <p className={`text-xl text-text-secondary mb-12 max-w-2xl mx-auto leading-relaxed transition-all duration-1000 delay-300 ${
              isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            } font-mono`}>
              Experience the future of AI-assisted development. Intelligent routing, 
              privacy-first design, and seamless multi-provider integration—all in one powerful platform.
            </p>

            {/* CTA Buttons */}
            <div className={`flex flex-col sm:flex-row gap-4 justify-center items-center transition-all duration-1000 delay-600 ${
              isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            }`}>
              <Button 
                onClick={handleGetStarted}
                size="lg"
                className="bg-accent-green text-bg-primary hover:bg-accent-green-bright font-semibold px-8 py-3 rounded-lg text-lg transition-all duration-300 hover:shadow-xl hover:shadow-accent-green/25 transform hover:-translate-y-1 glow"
              >
                Start Building
                <ArrowRight className="w-5 h-5 ml-3" />
              </Button>
              <Button 
                onClick={handleLearnMore}
                variant="outline"
                size="lg"
                className="border-border-medium text-text-primary hover:bg-bg-tertiary font-semibold px-8 py-3 rounded-lg text-lg transition-all duration-300 backdrop-blur-sm font-mono"
              >
                View Dashboard
              </Button>
            </div>

            {/* Stats */}
            <div className={`grid grid-cols-1 md:grid-cols-3 gap-8 mt-16 transition-all duration-1000 delay-900 ${
              isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            }`}>
              <div className="text-center group hover:bg-bg-tertiary p-6 rounded-xl transition-all duration-300">
                <div className="text-3xl font-bold text-accent-green mb-2">100%</div>
                <div className="text-text-secondary text-sm font-mono">Privacy First</div>
              </div>
              <div className="text-center group hover:bg-bg-tertiary p-6 rounded-xl transition-all duration-300">
                <div className="text-3xl font-bold text-info mb-2">Multi</div>
                <div className="text-text-secondary text-sm font-mono">Provider Support</div>
              </div>
              <div className="text-center group hover:bg-bg-tertiary p-6 rounded-xl transition-all duration-300">
                <div className="text-3xl font-bold text-warning mb-2">Smart</div>
                <div className="text-text-secondary text-sm font-mono">Routing</div>
              </div>
            </div>
          </div>
        </main>

        {/* Features Section */}
        <section className="container mx-auto px-6 pb-20">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="bg-bg-secondary border border-border-subtle rounded-xl p-6 hover:bg-bg-tertiary transition-all duration-300 group hover:-translate-y-2"
              >
                <div className="w-12 h-12 bg-gradient-to-r from-accent-green/20 to-info/20 rounded-xl flex items-center justify-center mb-4 group-hover:from-accent-green/40 group-hover:to-info/40 transition-all duration-300">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2 font-mono">{feature.title}</h3>
                <p className="text-text-secondary text-sm leading-relaxed font-mono">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Use Cases Section */}
        <section className="container mx-auto px-6 pb-20">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-text-primary mb-4 font-mono">Perfect For</h2>
            <p className="text-text-secondary text-lg font-mono">Discover how GoblinOS Assistant can transform your workflow</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {useCases.map((useCase, index) => (
              <div 
                key={index}
                className="bg-gradient-to-br from-bg-secondary to-bg-tertiary border border-border-medium rounded-2xl p-8 hover:from-bg-tertiary hover:to-bg-elevated transition-all duration-300 group hover:-translate-y-2"
              >
                <div className="w-16 h-16 bg-gradient-to-r from-accent-green/20 to-warning/20 rounded-2xl flex items-center justify-center mb-6 group-hover:from-accent-green/40 group-hover:to-warning/40 transition-all duration-300">
                  {useCase.icon}
                </div>
                <h3 className="text-2xl font-bold text-text-primary mb-4 font-mono">{useCase.title}</h3>
                <p className="text-text-secondary text-lg leading-relaxed font-mono">{useCase.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="container mx-auto px-6 pb-20">
          <div className="bg-gradient-to-r from-accent-green/20 to-info/20 border border-border-medium rounded-3xl p-12 text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-text-primary mb-6 font-mono">
              Ready to Supercharge Your Development?
            </h2>
            <p className="text-text-secondary text-lg mb-8 max-w-2xl mx-auto font-mono">
              Join developers who are already building the future with intelligent AI assistance.
              Get started in seconds and experience the difference.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                onClick={handleGetStarted}
                size="lg"
                className="bg-accent-green text-bg-primary hover:bg-accent-green-bright font-semibold px-10 py-4 rounded-lg text-lg transition-all duration-300 hover:shadow-xl hover:shadow-accent-green/25 transform hover:-translate-y-1 glow"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5 ml-3" />
              </Button>
              <Button 
                variant="outline"
                size="lg"
                className="border-border-medium text-text-primary hover:bg-bg-tertiary font-semibold px-10 py-4 rounded-lg text-lg transition-all duration-300 backdrop-blur-sm font-mono"
              >
                View Live Demo
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
