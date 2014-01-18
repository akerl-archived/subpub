module Subpub
  MESSAGE_SPEC = {
    timestamp: { mutable: false, default: proc { Time.now } },
    type: { mutable: false, required: true },
    weight: { mutable: true, default: 0 },
    name: { mutable: false, required: true },
    body: { mutable: false, required: true },
    location: { mutable: false, required: true },
    tags: { mutable: true, default: proc { [] } },
    attributes: { mutable: true, default: proc { {} } },
  }
    
  class Message
  end
end
