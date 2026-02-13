export const translations = {
  en: {
    // Common
    appName: 'Bus Booking',
    search: 'Search',
    cancel: 'Cancel',
    confirm: 'Confirm',
    save: 'Save',
    edit: 'Edit',
    delete: 'Delete',
    back: 'Back',
    next: 'Next',
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    noData: 'No data available',

    // Navigation
    home: 'Home',
    buses: 'Buses',
    myBookings: 'My Bookings',
    profile: 'Profile',
    logout: 'Logout',
    becomeOperator: 'Become Operator',

    // Home Page
    searchBuses: 'Search Buses',
    from: 'From',
    to: 'To',
    pickupDate: 'Pickup Date',
    returnDate: 'Return Date',
    passengers: 'Passengers',
    oneWay: 'One Way',
    roundTrip: 'Round Trip',
    
    // Bus Listing
    busType: 'Bus Type',
    seatingCapacity: 'Seating Capacity',
    pricePerKm: 'Price per KM',
    rating: 'Rating',
    reviews: 'Reviews',
    bookNow: 'Book Now',
    selectBus: 'Select Bus',

    // Booking
    bookingDetails: 'Booking Details',
    customerInfo: 'Customer Information',
    paymentMethod: 'Payment Method',
    totalPrice: 'Total Price',
    confirmBooking: 'Confirm Booking',
    bookingConfirmed: 'Booking Confirmed',

    // Payment
    proceedToPayment: 'Proceed to Payment',
    paymentFailed: 'Payment Failed',
    paymentSuccess: 'Payment Successful',
    upi: 'UPI',
    card: 'Credit/Debit Card',
    netBanking: 'Net Banking',
    payAtPickup: 'Pay at Pickup',

    // Operator Dashboard
    operatorDashboard: 'Operator Dashboard',
    myBuses: 'My Buses',
    earnings: 'Earnings',
    addBus: 'Add Bus',
    editBus: 'Edit Bus',
    busDetails: 'Bus Details',
    registrationNumber: 'Registration Number',
    acType: 'AC Type',
    amenities: 'Amenities',

    // Profile
    personalInfo: 'Personal Information',
    businessInfo: 'Business Information',
    bankDetails: 'Bank Details',
    documents: 'Documents',
    uploadDocument: 'Upload Document',

    // Messages
    loginRequired: 'Please login to continue',
    registrationSuccess: 'Registration successful',
    operatorRegistrationSuccess: 'Operator registration submitted. Awaiting verification.',
    bookingSuccess: 'Booking confirmed successfully',
  },
  hi: {
    // Common
    appName: 'बस बुकिंग',
    search: 'खोज',
    cancel: 'रद्द करें',
    confirm: 'पुष्टि करें',
    save: 'बचाएं',
    edit: 'संपादित करें',
    delete: 'हटाएं',
    back: 'पीछे',
    next: 'अगला',
    loading: 'लोड हो रहा है...',
    error: 'त्रुटि',
    success: 'सफल',
    noData: 'कोई डेटा उपलब्ध नहीं',

    // Navigation
    home: 'होम',
    buses: 'बसें',
    myBookings: 'मेरी बुकिंग',
    profile: 'प्रोफाइल',
    logout: 'लॉग आउट',
    becomeOperator: 'ऑपरेटर बनें',

    // Home Page
    searchBuses: 'बसें खोजें',
    from: 'से',
    to: 'तक',
    pickupDate: 'पिकअप की तारीख',
    returnDate: 'वापसी की तारीख',
    passengers: 'यात्री',
    oneWay: 'एक तरफा',
    roundTrip: 'राउंड ट्रिप',

    // Bus Listing
    busType: 'बस का प्रकार',
    seatingCapacity: 'बैठने की क्षमता',
    pricePerKm: 'प्रति किलोमीटर मूल्य',
    rating: 'रेटिंग',
    reviews: 'समीक्षाएं',
    bookNow: 'अभी बुक करें',
    selectBus: 'बस चुनें',

    // Booking
    bookingDetails: 'बुकिंग विवरण',
    customerInfo: 'ग्राहक जानकारी',
    paymentMethod: 'भुगतान विधि',
    totalPrice: 'कुल मूल्य',
    confirmBooking: 'बुकिंग की पुष्टि करें',
    bookingConfirmed: 'बुकिंग की पुष्टि हुई',

    // Payment
    proceedToPayment: 'भुगतान के लिए आगे बढ़ें',
    paymentFailed: 'भुगतान विफल',
    paymentSuccess: 'भुगतान सफल',
    upi: 'यूपीआई',
    card: 'क्रेडिट/डेबिट कार्ड',
    netBanking: 'नेट बैंकिंग',
    payAtPickup: 'पिकअप पर भुगतान करें',

    // Operator Dashboard
    operatorDashboard: 'ऑपरेटर डैशबोर्ड',
    myBuses: 'मेरी बसें',
    earnings: 'कमाई',
    addBus: 'बस जोड़ें',
    editBus: 'बस संपादित करें',
    busDetails: 'बस विवरण',
    registrationNumber: 'पंजीकरण संख्या',
    acType: 'एसी प्रकार',
    amenities: 'सुविधाएं',

    // Profile
    personalInfo: 'व्यक्तिगत जानकारी',
    businessInfo: 'व्यावसायिक जानकारी',
    bankDetails: 'बैंक विवरण',
    documents: 'दस्तावेज़',
    uploadDocument: 'दस्तावेज़ अपलोड करें',

    // Messages
    loginRequired: 'जारी रखने के लिए कृपया लॉगिन करें',
    registrationSuccess: 'पंजीकरण सफल',
    operatorRegistrationSuccess: 'ऑपरेटर पंजीकरण सफलतापूर्वक सबमिट किया गया। सत्यापन की प्रतीक्षा करें।',
    bookingSuccess: 'बुकिंग सफलतापूर्वक की गई',
  },
};

export const t = (key: string, language: 'en' | 'hi' = 'en') => {
  return (translations[language] as any)[key] || key;
};
