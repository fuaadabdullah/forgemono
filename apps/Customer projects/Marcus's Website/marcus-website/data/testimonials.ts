export interface Testimonial {
  name: string;
  rating: number;
  text: string;
  vehicle: string;
  service: string;
}

export const testimonials: Testimonial[] = [
  {
    name: "Jennifer Martinez",
    rating: 5,
    text: "Marcus saved me hundreds by diagnosing my brake issue correctly the first time. He came to my office during lunch and had my car fixed in under an hour. The brake pads he installed are top quality and the price was very reasonable. I won't trust anyone else with my car now!",
    vehicle: "BMW X3 2016",
    service: "Brake Service"
  },
  {
    name: "David Thompson",
    rating: 5,
    text: "Had a complete breakdown on the highway at 2 AM. Called Marcus and he was there within 45 minutes! His mobile service got me back on the road safely. He explained everything clearly and didn't try to sell me unnecessary work. His honesty and professionalism are unmatched.",
    vehicle: "Chevrolet Silverado 2020",
    service: "Emergency Repair"
  },
  {
    name: "Maria Gonzalez",
    rating: 5,
    text: "I've been taking my car to Marcus for 3 years now. His attention to detail is incredible - he caught a small oil leak before it became a major problem. His mobile service means I don't have to waste time at a shop. The best mechanic I've ever worked with!",
    vehicle: "Honda Accord 2019",
    service: "Oil Change & Maintenance"
  },
  {
    name: "Robert Kim",
    rating: 5,
    text: "Marcus rebuilt my engine and brought my classic Mustang back to life. His knowledge of older vehicles is impressive, and he treated my car like it was his own. The work was done at my garage and the quality exceeded my expectations. Worth every penny!",
    vehicle: "Ford Mustang 1998",
    service: "Engine Rebuild"
  },
  {
    name: "Amanda Foster",
    rating: 5,
    text: "As a single mom, I don't have time to drop off my car at a shop. Marcus comes to my house and does all the maintenance while I work from home. He's always on time, explains everything clearly, and my car has never run better. Highly recommend for busy families!",
    vehicle: "Toyota Highlander 2018",
    service: "Full Service Maintenance"
  },
  {
    name: "Carlos Ramirez",
    rating: 5,
    text: "Marcus diagnosed a transmission issue that three other shops couldn't figure out. His advanced diagnostic equipment and experience made all the difference. He even coordinated towing when needed. Professional, honest, and skilled - the complete package!",
    vehicle: "GMC Yukon 2017",
    service: "Transmission Repair"
  }
];
